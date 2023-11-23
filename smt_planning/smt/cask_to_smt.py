import json 
import time


from z3 import Solver, sat, unsat, Bool
from smt_planning.smt.StateHandler import StateHandler
from smt_planning.dicts.PropertyDictionary import PropertyDictionary
from smt_planning.dicts.CapabilityDictionary import CapabilityDictionary
from smt_planning.smt.variable_declaration import getAllProperties, get_provided_capabilities
from smt_planning.smt.capability_preconditions import getCapabilityPreconditions
from smt_planning.smt.capability_effects import getCapabilityEffects
from smt_planning.smt.capability_constraints import getCapabilityConstraints
from smt_planning.smt.bool_variable_support import getPropositionSupports
from smt_planning.smt.constraints_bools import get_bool_constraints
from smt_planning.smt.constraints_real_variables import get_variable_constraints
from smt_planning.smt.property_links import get_property_cross_relations
from smt_planning.smt.init import get_init
from smt_planning.smt.goal import get_goal
from smt_planning.smt.real_variable_contin_change import get_real_variable_continuous_changes
from smt_planning.smt.planning_result import PlanningResult
from smt_planning.smt.query_handlers import FileQueryHandler, SparqlEndpointQueryHandler


class CaskadePlanner:

	def with_file_query_handler(self, filename):
		self.query_handler = FileQueryHandler(filename)

	def with_endpoint_query_handler(self, endpoint_url):
		self.query_handler = SparqlEndpointQueryHandler(endpoint_url)

	def add_comment(self, solver: Solver, comment_text: str):
		# Adds a comment to the smt output in a pretty hackish way: 
		# Z3 doesn't allow adding comments, so we create a variable with the comment as its name and add it to the solver

		comment = Bool(f"## {comment_text} ##")
		solver.add(comment)

	def cask_to_smt(self, max_happenings: int = 5, problem_location: str = "problem.smt" , result_location:str = "result.json", model_location: str = "model.json"):

		start_time = time.time()
		state_handler = StateHandler()


		happenings = 0
		# Fixed upper bound for number of events in one happening. Currently no events, so we just have the start and end of a happening
		event_bound = 2
		solver_result = unsat

		while (happenings <= max_happenings and solver_result == unsat):
			# SMT Solver
			solver = Solver()
			solver.reset()
			state_handler.reset_caches()
			solver_result = unsat
			happenings += 1

			# ------------------------------Variable Declaration------------------------------------------ 	
			# Get all properties connected to provided capabilities as inputs or outputs
			property_dictionary = getAllProperties(happenings, event_bound, self.query_handler)
			state_handler.set_property_dictionary(property_dictionary)

			# Get provided capabilities and transform to boolean SMT variables
			capability_dictionary = get_provided_capabilities(happenings, self.query_handler)
			state_handler.set_capability_dictionary(capability_dictionary)

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
			preconditions = getCapabilityPreconditions(happenings, event_bound, self.query_handler)
			for precondition in preconditions:
				solver.add(precondition)

			# --------------------------------------- Capability Effect ---------------------------------------
			self.add_comment(solver, "Start of effects")
			effects = getCapabilityEffects(happenings, event_bound, self.query_handler)
			for effect in effects:
				solver.add(effect)

			# Capability constraints are expressions in smt2 form that cannot be added programmatically. Thus, we take the current solver in string form
			# We create a new solver object. Then we take the current solver string and add the constraint strings. We then re-import everything back into the fresh solver object
			# It has to be a fresh object because just re-importing doesn't clear everything
			self.add_comment(solver, "Start of capability constraints")
			current_solver_string = solver.to_smt2()
			solver = Solver()
			constraints = getCapabilityConstraints(happenings, event_bound, self.query_handler)
			for constraint in constraints:
				current_solver_string += f"\n{constraint}" 

			solver.from_string(current_solver_string)

			# ---------------- Constraints Capability mutexes (H14) -----------------------------------------


			# ---------------- Init  --------------------------------------------------------
			self.add_comment(solver, "Start of init")
			inits = get_init(self.query_handler)
			for init in inits:
				solver.add(init)												

			# ---------------------- Goal ------------------------------------------------- 
			self.add_comment(solver, "Start of goal")
			goals = get_goal(happenings, self.query_handler)
			for goal in goals:
				solver.add(goal)

			# Product Goal (aus Req Cap)

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

			end_time = time.time()
			print(f"Time for generating SMT: {end_time - start_time}")

			# smtlib code  
			# print(solver.to_smt2())
			with open(problem_location, 'w') as file:
				file.write(solver.to_smt2())
			

			# Check satisfiability and get the model
			solver_result = solver.check()
			end_time_solver = time.time()
			print(f"Time for solving SMT: {end_time_solver - end_time}")

			if solver_result == unsat:
				print(f"No solution with {happenings} happening(s) found.")
			else:
				model = solver.model()
				result = PlanningResult(model, problem_location, result_location, model_location)

				# Write the model to a JSON file
				with open(result_location, 'w') as json_file:
					json.dump(result, json_file, default=lambda o: o.as_dict(), indent=4)
				return result 


if __name__ == '__main__': 
	ontology_file = 'ex_two_caps.ttl'
	max_happenings = 3
	problem_location = "problem.smt"
	result_location = 'plan.json'
	model_location = 'model.json'
	planner = CaskadePlanner()
	planner.with_file_query_handler(ontology_file)
	planner.cask_to_smt(max_happenings, problem_location, result_location, model_location)
