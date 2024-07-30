import json 
import time

from smt_planning.ontology_handling.query_handlers import FileQueryHandler, SparqlEndpointQueryHandler
from z3 import Solver, Optimize, unsat, Bool, Sum, BoolRef, parse_smt2_string
from smt_planning.smt.StateHandler import StateHandler
from smt_planning.openmath.parse_openmath import QueryCache
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
from smt_planning.smt.property_links import get_property_cross_relations
from smt_planning.smt.init import init_smt
from smt_planning.smt.goal import goal_smt
from smt_planning.smt.real_variable_contin_change import get_real_variable_continuous_changes
from smt_planning.smt.capability_mutexes import get_capability_mutexes
from smt_planning.smt.planning_result import PlanningResult

class CaskadePlanner:

	assertion_dictionary = {}

	def with_file_query_handler(self, filename: str):
		self.query_handler = FileQueryHandler(filename)

	def with_endpoint_query_handler(self, endpoint_url):
		self.query_handler = SparqlEndpointQueryHandler(endpoint_url)

	def add_comment(self, solver: Solver, comment_text: str):
		# Adds a comment to the smt output in a pretty hackish way: 
		# Z3 doesn't allow adding comments, so we create a variable with the comment as its name and add it to the solver

		comment = Bool(f"## {comment_text} ##")
		solver.add(comment)

	def cask_to_smt(self, max_happenings: int = 5, problem_location = None, model_location = None, plan_location = None):

		start_time = time.time()
		state_handler = StateHandler()
		state_handler.set_query_handler(self.query_handler)

		happenings = 0
		# Fixed upper bound for number of events in one happening. Currently no events, so we just have the start and end of a happening
		event_bound = 2
		solver_result = unsat

		# needs to be reset for new planning request, otherwise it will keep the old data annd not be able to solve the problem at all or solve the problem incorrectly
		QueryCache.reset()
			
		# Get all properties connected to provided capabilities as inputs or outputs as well as all instance descriptions 
		property_dictionary = get_all_properties()
		state_handler.set_property_dictionary(property_dictionary)

		# Get provided capabilities and their influence on output objects as well as resources that provide capabilities
		cap_and_res_dictionary = get_provided_capabilities()
		capability_dictionary = cap_and_res_dictionary[0]
		resource_dictionary = cap_and_res_dictionary[1]
		state_handler.set_capability_dictionary(capability_dictionary)
		state_handler.set_resource_dictionary(resource_dictionary)

		# Capability Constraints
		get_capability_constraints()

		# Get all inits and goals of planning problem based on the instance descriptions
		get_init()

		while (happenings <= max_happenings and solver_result == unsat):
			# SMT Solver
			solver = Solver()
			solver.set(unsat_core=True)
			solver.reset()
			state_handler.reset_caches()
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
			preconditions = capability_preconditions_smt(happenings, event_bound)
			precondition_counter = 0
			for precondition in preconditions:
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

			# Capability constraints are expressions in smt2 form that cannot be added programmatically, because we only have the whole expression in string form 
			# after parsing it from OpenMath RDF. Hence, we must read it as string into a temp solver and then add all assertions into our main solver
			self.add_comment(solver, "Start of capability constraints")
			# current_solver_string = solver.to_smt2()
			
			temp_solver = Solver()
			main_solver_state = solver.to_smt2()
			temp_solver_string = "\n".join(
				line for line in main_solver_state.splitlines() if line.startswith("(declare-fun")
			)
			
			# Füge die ursprünglichen Variablen wieder hinzu
			# temp_solver.from_string(variables_state)

			# temp_solver_string = ""
			constraints = capability_constraints_smt(happenings, event_bound)
			for constraint in constraints:
				temp_solver_string += f"\n{constraint}" 

			temp_solver.from_string(temp_solver_string)
			temp_solver_assertions = temp_solver.assertions()

			# add all assertions back into main solver
			cap_constraint_counter = 0
			for capability_constraint_assertion in temp_solver_assertions:
				cap_constraint_counter += 1
				assertion_name = f'capConstraint_{cap_constraint_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = capability_constraint_assertion
				solver.assert_and_track(capability_constraint_assertion, assertion_name)

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
			inits = init_smt()
			init_counter = 0
			for init in inits:
				init_counter += 1
				assertion_name = f'init_{init_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = init
				solver.assert_and_track(init, assertion_name)

			# ---------------------- Goal ------------------------------------------------- 
			self.add_comment(solver, "Start of goal")
			goals = goal_smt()
			goal_counter = 0
			for goal in goals:
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
			self.add_comment(solver, "Start of related properties")
			property_cross_relations = get_property_cross_relations(happenings, event_bound)
			cross_relation_counter = 0
			for cross_relation in property_cross_relations:
				cross_relation_counter += 1
				assertion_name = f'crossRelation_{cross_relation_counter}_{happenings}'
				self.assertion_dictionary[assertion_name] = cross_relation
				solver.assert_and_track(cross_relation, assertion_name)

			# Optimize by minimizing number of used capabilities to prevent unnecessary use of capabilities
			#constraints = solver.assertions()
			# opt = Optimize()
			# opt.add(constraints)

			#capabilities = [occurrence.z3_variable for capability in capability_dictionary.capabilities.values() for occurrence in capability.occurrences.values()]
			# opt.minimize(Sum(capabilities))

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
					constraint_name = model_declaration.name()
					if constraint_name in self.assertion_dictionary:
						replaced_model[self.assertion_dictionary[constraint_name]] = model[model_declaration]
					else:
						replaced_model[constraint_name] = model[model_declaration]
				print(model)
				print(replaced_model)
				plan = PlanningResult(model)

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
						json.dump(plan, json_file, default=lambda o: o.as_dict(), indent=4)


				return plan
		unsat_core = solver.unsat_core()

def is_unsat_core(solver, core):
    s = Solver()
    for c in core:
        s.add(c)
    return s.check() == unsat

def find_minimal_unsat_core(solver, core):
    if not is_unsat_core(solver, core):
        return []
    for i in range(len(core)):
        reduced_core = core[:i] + core[i+1:]
        if is_unsat_core(solver, reduced_core):
            return find_minimal_unsat_core(solver, reduced_core)
    return core
