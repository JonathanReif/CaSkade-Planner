from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import json 
import time

from smt_planning.ontology_handling.query_handlers import FileQueryHandler, SparqlEndpointQueryHandler
from z3 import Solver, Optimize, unsat, Bool, Sum
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

		# Fixed upper bound for number of events in one happening. Currently no events, so we just have the start and end of a happening
		event_bound = 2

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

		with ThreadPoolExecutor() as executor:
			futures = {executor.submit(self.solve_happening, h, event_bound, problem_location = None, model_location = None, plan_location = None): h for h in range(max_happenings + 1)}

			for future in as_completed(futures):
				happenings = futures[future]
				try: 
					plan = future.result()
					if plan:
						end_time_solver = time.time()
						print(f"Solution found with {happenings} happenings in {end_time_solver - start_time} seconds.")
						return plan
				except Exception as e:
					print(f"Exception for {happenings} happenings: {e}")

		print("No solution found.")
		return None

	def solve_happening(self, happenings: int, event_bound: int, problem_location = None, model_location = None, plan_location = None):
		
		start_time = time.time()

		# SMT Solver
		solver = Solver()
		solver.reset()
		state_handler = StateHandler()
		state_handler.reset_caches()
		# TODO: Maybe work with deep copies of the state_handler or dictionaries to prevent data from being used in multiple threads
		solver_result = unsat

		# ------------------------------Variable Declaration------------------------------------------ 	
		# Get all properties connected to provided capabilities as inputs or outputs
		property_dictionary = create_property_dictionary_with_occurrences(happenings, event_bound)

		# Get provided capabilities and transform to boolean SMT variables
		capability_dictionary = create_capability_dictionary_with_occurrences(happenings)

		# ------------------------------Ressource IDs---------------------------------------------------
		self.add_comment(solver, "Start of resource ids")
		resource_ids = create_resource_ids(happenings, event_bound)
		for resource_id in resource_ids:
			solver.add(resource_id)

		# ------------------------Constraint Proposition (H1 + H2) --> bool properties------------------
		self.add_comment(solver, "Start of constraints proposition")
		bool_constraints = get_bool_constraints(happenings, event_bound)
		for bool_constraint in bool_constraints:
			solver.add(bool_constraint)	

		# ---------------------Constraint Real Variable (H5) --> real properties-----------------------------
		self.add_comment(solver, "Start of constraints real variables")
		variable_constraints = get_variable_constraints(happenings, event_bound)
		for variable_constraint in variable_constraints:
			solver.add(variable_constraint)	

		# ----------------- Capability Precondition ------------------------------------------------------
		self.add_comment(solver, "Start of preconditions")
		preconditions = capability_preconditions_smt(happenings, event_bound)
		for precondition in preconditions:
			solver.add(precondition)

		# --------------------------------------- Capability Effect ---------------------------------------
		self.add_comment(solver, "Start of effects")
		effects = capability_effects_smt(happenings, event_bound)
		for effect in effects:
			solver.add(effect)

		# Capability constraints are expressions in smt2 form that cannot be added programmatically. Thus, we take the current solver in string form
		# We create a new solver object. Then we take the current solver string and add the constraint strings. We then re-import everything back into the fresh solver object
		# It has to be a fresh object because just re-importing doesn't clear everything
		self.add_comment(solver, "Start of capability constraints")
		current_solver_string = solver.to_smt2()
		solver = Solver()
		constraints = capability_constraints_smt(happenings, event_bound)
		for constraint in constraints:
			current_solver_string += f"\n{constraint}" 

		solver.from_string(current_solver_string)

		# ---------------- Constraints Capability mutexes (H14) -----------------------------------------
		self.add_comment(solver, "Start of capability mutexes")
		capability_mutexes = get_capability_mutexes(happenings)
		for capability_mutex in capability_mutexes:
			solver.add(capability_mutex)		

		# ---------------- Init  --------------------------------------------------------
		self.add_comment(solver, "Start of init")
		inits = init_smt()
		for init in inits:
			solver.add(init)												

		# ---------------------- Goal ------------------------------------------------- 
		self.add_comment(solver, "Start of goal")
		goals = goal_smt()
		for goal in goals:
			solver.add(goal)

		# ------------------- Proposition support (P5 + P6) ----------------------------
		self.add_comment(solver, "Start of proposition support")
		proposition_supports = getPropositionSupports(happenings, event_bound)
		for support in proposition_supports:
			solver.add(support)

		# ----------------- Continuous change on real variables (P11) ------------------
		self.add_comment(solver, "Start of real variable continuous change")
		real_variable_cont_changes = get_real_variable_continuous_changes(happenings, event_bound)
		for real_variable_cont_change in real_variable_cont_changes:
			solver.add(real_variable_cont_change)

		# ----------------- Cross-connection of related properties (new) -----------------
		self.add_comment(solver, "Start of related properties")
		property_cross_relations = get_property_cross_relations(happenings, event_bound)
		for cross_relation in property_cross_relations:
			solver.add(cross_relation)

		# Optimize by minimizing number of used capabilities to prevent unnecessary use of capabilities
		constraints = solver.assertions()
		opt = Optimize()
		opt.add(constraints)

		capabilities = [occurrence.z3_variable for capability in capability_dictionary.capabilities.values() for occurrence in capability.occurrences.values()]
		opt.minimize(Sum(capabilities))

		end_time = time.time()
		print(f"Time for generating SMT: {end_time - start_time}")	

		# Check satisfiability and get the model
		solver_result = opt.check()
		end_time_solver = time.time()
		print(f"Time for solving SMT: {end_time_solver - end_time}")

		if solver_result == unsat:
			print(f"No solution with {happenings} happening(s) found.")
			return None
		else:
			model = opt.model()
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
