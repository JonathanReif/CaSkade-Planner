import json 
import time

from typing import List

from smt_planning.ontology_handling.query_handlers import FileQueryHandler, SparqlEndpointQueryHandler
from smt_planning.planning_result import PlanningResultType, PlanningResult
from smt_planning.dicts.PropertyDictionary import Property
from z3 import Solver, Optimize, unsat, Bool, Real, RealSort, IntSort, BoolSort, Z3_OP_IMPLIES
from smt_planning.smt.StateHandler import StateHandler
from smt_planning.openmath.parse_openmath import QueryCache
from smt_planning.smt.property_links import get_related_properties, set_required_capability, reset_property_pairs
from smt_planning.ontology_handling.capability_and_property_query import get_all_properties, get_provided_capabilities
from smt_planning.ontology_handling.init_query import get_init
from smt_planning.ontology_handling.capability_constraints_query import get_capability_constraints
from smt_planning.smt.variable_declaration import create_property_dictionary_with_occurrences, create_capability_dictionary_with_occurrences, create_resource_ids
from smt_planning.smt.capability_preconditions import capability_preconditions_smt
from smt_planning.smt.capability_effects import capability_effects_smt
from smt_planning.smt.capability_constraints import capability_constraints_smt
from smt_planning.smt.bool_variable_support import getPropositionSupports
from smt_planning.smt.constraints_bools import get_bool_constraints
from smt_planning.smt.constraints_real_variables import get_variable_constraints
from smt_planning.smt.init import init_smt
from smt_planning.smt.goal import goal_smt
from smt_planning.smt.real_variable_contin_change import get_real_variable_continuous_changes
from smt_planning.smt.capability_mutexes import get_capability_mutexes
from smt_planning.smt.fix_constants import fix_constants

class CaskadePlanner:

	assertion_dictionary = {}
	required_capability_iri: str

	def __init__(self, required_capability_iri: str) -> None:
		self.required_capability_iri = required_capability_iri

	def with_file_query_handler(self, filename: str):
		self.query_handler = FileQueryHandler(filename)

	def with_endpoint_query_handler(self, endpoint_url):
		self.query_handler = SparqlEndpointQueryHandler(endpoint_url)

	def add_comment(self, solver: Solver, comment_text: str):
		# Adds a comment to the smt output in a pretty hackish way: 
		# Z3 doesn't allow adding comments, so we create a variable with the comment as its name and add it to the solver

		comment = Bool(f"## {comment_text} ##")
		solver.add(comment)

	def cask_to_smt(self, max_happenings: int = 5, problem_location = None, model_location = None, plan_location = None) -> PlanningResult:
		print("Started planning. This may take a while...")
		start_time = time.time()
		state_handler = StateHandler()
		state_handler.set_query_handler(self.query_handler)
		reset_property_pairs()

		# Set required cap to property link finding. TODO: Could be better moved to state handler
		set_required_capability(self.required_capability_iri)

		happenings = 0
		# Fixed upper bound for number of events in one happening. Currently no events, so we just have the start and end of a happening
		event_bound = 2
		solver_result = unsat

		# needs to be reset for new planning request, otherwise it will keep the old data annd not be able to solve the problem at all or solve the problem incorrectly
		QueryCache.reset()
		# state_handler.reset_caches()
			
		# Get all properties connected to provided capabilities as inputs or outputs as well as all instance descriptions 
		property_dictionary = get_all_properties(self.required_capability_iri)
		state_handler.set_property_dictionary(property_dictionary)
		# PropertyPairCache.get_property_pairs(self.required_capability_iri)

		# Get provided capabilities and their influence on output objects as well as resources that provide capabilities
		cap_and_res_dictionary = get_provided_capabilities(self.required_capability_iri)
		capability_dictionary = cap_and_res_dictionary[0]
		resource_dictionary = cap_and_res_dictionary[1]
		state_handler.set_capability_dictionary(capability_dictionary)
		state_handler.set_resource_dictionary(resource_dictionary)

		# Capability Constraints to store
		# // TODO: Do we really need this?
		get_capability_constraints()
		
		# Get all inits and goals of planning problem based on the instance descriptions
		# get_init()

		while (happenings < max_happenings and solver_result == unsat):
			# SMT Solver
			solver = Solver()
			solver.set(unsat_core=True)
			solver.reset()
			
			solver_result = unsat
			happenings += 1

			# ------------------------------Variable Declaration------------------------------------------ 	
			# Get all properties connected to provided capabilities as inputs or outputs
			create_property_dictionary_with_occurrences(happenings, event_bound)

			# Get provided capabilities and transform to boolean SMT variables
			create_capability_dictionary_with_occurrences(happenings)

			# ------------------------------Ressource IDs---------------------------------------------------
			self.add_comment(solver, "Start of resource ids")
			resource_ids = create_resource_ids(happenings, event_bound)
			resource_id_counter = 0
			for resource_id in resource_ids:
				resource_id_counter += 1
				assertion_name = f'resourceId_{resource_id_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = resource_id
				solver.assert_and_track(resource_id, assertion_name)

			# ------------------------Constraint Proposition (H1 + H2) --> bool properties------------------
			self.add_comment(solver, "Start of constraints proposition")
			bool_constraints = get_bool_constraints(happenings, event_bound)
			bool_constraint_counter = 0
			for bool_constraint in bool_constraints:
				bool_constraint_counter += 1
				assertion_name = f'boolConstraint_{bool_constraint_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = bool_constraint
				solver.assert_and_track(bool_constraint, assertion_name)

			# ---------------------Constraint Real Variable (H5) --> real properties-----------------------------
			self.add_comment(solver, "Start of constraints real variables")
			variable_constraints = get_variable_constraints(happenings, event_bound)
			variable_constraint_counter = 0
			for variable_constraint in variable_constraints:
				variable_constraint_counter += 1
				assertion_name = f'varConstraint_{variable_constraint_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = variable_constraint
				solver.assert_and_track(variable_constraint, assertion_name)

			# ----------------- Capability Precondition ------------------------------------------------------
			self.add_comment(solver, "Start of preconditions")
			precondition_constraints = capability_preconditions_smt(happenings, event_bound)
			precondition_counter = 0
			for precondition in precondition_constraints:
				precondition_counter += 1
				assertion_name = f'precond_{precondition_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = precondition
				solver.assert_and_track(precondition, assertion_name)

			# --------------------------------------- Capability Effect ---------------------------------------
			self.add_comment(solver, "Start of effects")
			effects = capability_effects_smt(happenings, event_bound)
			effect_counter = 0
			for effect in effects:
				effect_counter += 1
				assertion_name = f'effect_{effect_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = effect
				solver.assert_and_track(effect, assertion_name)

			# ---------------- Constraints Capability mutexes (H14) -----------------------------------------
			self.add_comment(solver, "Start of capability mutexes")
			capability_mutexes = get_capability_mutexes(happenings)
			capability_mutex_counter = 0
			for capability_mutex in capability_mutexes:
				capability_mutex_counter += 1
				assertion_name = f'capMutex_{capability_mutex_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = capability_mutex
				solver.assert_and_track(capability_mutex, assertion_name)

			# ---------------- Init  --------------------------------------------------------
			self.add_comment(solver, "Start of init")
			init_constraints = init_smt()
			init_counter = 0
			for init in init_constraints:
				init_counter += 1
				assertion_name = f'init_{init_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = init
				solver.assert_and_track(init, assertion_name)

			# ---------------------- Goal ------------------------------------------------- 
			self.add_comment(solver, "Start of goal")
			goal_constraints = goal_smt(happenings)
			goal_counter = 0
			for goal in goal_constraints:
				goal_counter += 1
				assertion_name = f'goal_{goal_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = goal
				solver.assert_and_track(goal, assertion_name)

			# ------------------- Proposition support (P5 + P6) ----------------------------
			self.add_comment(solver, "Start of proposition support")
			proposition_supports = getPropositionSupports(happenings, event_bound)
			suppport_counter = 0
			for support in proposition_supports:
				suppport_counter += 1
				assertion_name = f'support_{suppport_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = support
				solver.assert_and_track(support, assertion_name)

			# ----------------- Continuous change on real variables (P11) ------------------
			self.add_comment(solver, "Start of real variable continuous change")
			real_variable_cont_changes = get_real_variable_continuous_changes(happenings, event_bound)
			real_variable_cont_change_counter = 0
			for real_variable_cont_change in real_variable_cont_changes:
				real_variable_cont_change_counter += 1
				assertion_name = f'realVarContChange_{real_variable_cont_change_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = real_variable_cont_change
				solver.assert_and_track(real_variable_cont_change, assertion_name)

			# ----------------- Cross-connection of related properties (new) -----------------
			# self.add_comment(solver, "Start of related properties")
			# property_cross_relations = get_property_cross_relations(happenings, event_bound)
			# cross_relation_counter = 0
			# for cross_relation in property_cross_relations:
			# 	cross_relation_counter += 1
			# 	assertion_name = f'crossRelation_{cross_relation_counter}_{happenings}'
			# 	self.assertion_dictionary[assertion_name] = cross_relation
			# 	solver.assert_and_track(cross_relation, assertion_name)


			# Capability constraints are expressions in smt2 form that cannot be added programmatically, because we only have the whole expression in string form 
			# after parsing it from OpenMath RDF. Hence, we must read it as string into a temp solver and then add all assertions into our main solver
			self.add_comment(solver, "Start of capability constraints")
			temp_solver = Solver()
			# Add property z3 variables (they are needed for constraints in the next step)
			temp_solver_string = "\n".join(
				[f'(declare-fun {occurrence.z3_variable.sexpr()} () {occurrence.type})' for occurrence in property_dictionary.get_all_property_occurences()]
			)
			# Add capability z3 variables (they are needed for constraints in the next step)
			temp_solver_string += "\n".join(
				[f'(declare-fun {occurrence.z3_variable.sexpr()} () Bool)' for occurrence in capability_dictionary.get_all_capability_occurrences()]
			)
			# Add constraints
			constraints = capability_constraints_smt(happenings, event_bound)
			for constraint in constraints:
				temp_solver_string += f"\n{constraint}" 

			temp_solver.from_string(temp_solver_string)
			temp_solver_assertions = temp_solver.assertions()

			# add all assertions back into main solver, now with tracking
			cap_constraint_counter = 0
			for capability_constraint_assertion in temp_solver_assertions:
				cap_constraint_counter += 1
				assertion_name = f'capConstraint_{cap_constraint_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = capability_constraint_assertion
				solver.assert_and_track(capability_constraint_assertion, assertion_name)

			constant_expressions = fix_constants(property_dictionary, capability_dictionary, happenings, event_bound)
			constant_counter = 0
			for constant_expression in constant_expressions:
				constant_counter += 1
				assertion_name = f'constant_{constant_counter}'
				self.assertion_dictionary[assertion_name] = constant_expression
				solver.assert_and_track(constant_expression, assertion_name)
				
			# Optimize by minimizing number of used capabilities to prevent unnecessary use of capabilities
			#constraints = solver.assertions()
			# opt = Optimize()
			# opt.add(constraints)

			#capabilities = [occurrence.z3_variable for capability in capability_dictionary.capabilities.values() for occurrence in capability.occurrences.values()]
			# opt.minimize(Sum(capabilities))

			# Important. All the related props of output values at 0_0 need to be bound. Otherwise if they are floating, the goal at happening_1 value can be taken for 0_0. 
			# This in turn leads to no capabilities getting invoked
			for goal in property_dictionary.goals:
				# add all goals themselves as we need to look into them as well. NO, DONT
				# properties_related_to_goal.append(property_dictionary.get_property(goal))
				properties_related_to_goal = get_related_properties(goal)
				
				# If a single one of the properties related to goal is bound, we can skip it. Else, bind
				# any(find_variable_in_expression(child, variable) for child in expression.children())
				# if any(is_variable_asserted(solver, property_dictionary.get_property_occurence(goal_prop.iri, 0, 0).z3_variable) for goal_prop in properties_related_to_goal): continue

				for goal_related_prop in properties_related_to_goal:
					var = property_dictionary.get_property_occurence(goal_related_prop.iri, 0, 0).z3_variable
					# TODO:checking for assertions is very expensive (recursive check in every loop). We should store all asserted vars to make checking faster
					if is_variable_asserted(solver, var): continue
					
					if var.sort() == BoolSort(): 
						goal_binding_assertion = var == False
					if var.sort() == IntSort(): 
						goal_binding_assertion = var == 0	# Maybe use better default?
					if var.sort() == RealSort(): 
						goal_binding_assertion = var == 0	# Maybe use better default?
					
					assertion_name = f"bind_{var}_{happenings}"
					self.assertion_dictionary[assertion_name] = goal_binding_assertion
					solver.assert_and_track(goal_binding_assertion, assertion_name)

			end_time = time.time()
			print(f"Time for generating SMT: {end_time - start_time}")	

			# Check satisfiability and get the model
			solver_result = solver.check()
			end_time_solver = time.time()
			print(f"Time for solving SMT: {end_time_solver - end_time}")

			if solver_result == unsat:
				print(f"No solution with {happenings} happening(s) found.")
			else:
				model = solver.model()
				replaced_model = {}
				for model_declaration in model.decls():
					declaration_name = model_declaration.name()
					if declaration_name in self.assertion_dictionary:
						continue
						# replaced_model[self.assertion_dictionary[declaration_name]] = model[model_declaration]
					else:
						replaced_model[declaration_name] = model[model_declaration]
				
				# Create the result
				result = PlanningResult(PlanningResultType.SAT, replaced_model, None)

				# Optional: store outputs in file
				if problem_location:
					# if problem_location is passed, store problem
					with open(problem_location, 'w') as file:
						file.write(solver.to_smt2())

				if model_location:
					# if model_location is passed, store model untransformed
					model_dict = {}
					for var in model:
						model_dict[str(var)] = str(model[var])
					with open(model_location, 'w') as file:
						json.dump(model_dict, file, indent=4)

				if plan_location:
					# if plan_location is passed, store model after transformation to better JSON
					with open(plan_location, 'w') as json_file:
						json.dump(result, json_file, default=lambda o: o.to_json(), indent=4)

				
				return result
		
		unsat_core = solver.unsat_core()
		# Retransform unsat core to insert original properties instead of assertion_name
		transformed_unsat_core = []
		for core in unsat_core:
			core_elem = self.assertion_dictionary[str(core)]
			transformed_unsat_core.append(core_elem)

		muc = find_minimal_unsat_core(transformed_unsat_core)
		unsat_core_string = []
		for core in muc:
			unsat_core_string.append(str(core))
		result = PlanningResult(PlanningResultType.UNSAT, None, unsat_core_string)
		end_time_muc = time.time()
		print(f"Time for finding MUC: {end_time_muc - end_time_solver}")
		return result



def is_unsat_core(core):
    s = Solver()
    for c in core:
        s.add(c)
    return s.check() == unsat

def find_minimal_unsat_core(core):
    # Überprüfen, ob der initiale Core unsatisfiable ist
    if not is_unsat_core(core):
        return core
    
    # Versuche, eine minimale unsatisfiable Menge zu finden
    for i in range(len(core)):
        reduced_core = core[:i] + core[i+1:]
        if is_unsat_core(reduced_core):
            return find_minimal_unsat_core(reduced_core)
    
    # Wenn keine Verkleinerung möglich ist, gebe den aktuellen Core zurück
    return core


# Checks if a variable is already asserted
def find_variable_in_expression(expression, variable):
	# The first layer of equations consists of implies because of all the names needed for unsat cores. 
	# But if in the lower layers, the type is an IMPLIES, we can skip it as such a constraint cannot be a binding of the var anymore
	if any(child.decl().kind() == Z3_OP_IMPLIES for child in expression.children()) :
		return False
	if expression == variable:
		return True
	return any(find_variable_in_expression(child, variable) for child in expression.children())

def is_variable_asserted(solver, variable):
    for assertion in solver.assertions():
        if find_variable_in_expression(assertion, variable):
            return True
    return False