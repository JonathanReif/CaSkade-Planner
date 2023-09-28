import json 
import time

from rdflib import Graph
from z3 import Solver, sat, unsat, Bool
from smt_planning.StateHandler import StateHandler
from smt_planning.dicts.PropertyDictionary import PropertyDictionary
from smt_planning.dicts.CapabilityDictionary import CapabilityDictionary
from smt_planning.variable_declaration import getAllProperties, get_provided_capabilities
from smt_planning.capability_preconditions import getCapabilityPreconditions
from smt_planning.capability_effects import getCapabilityEffects
from smt_planning.capability_constraints import getCapabilityConstraints
from smt_planning.bool_variable_support import getPropositionSupports
from smt_planning.constraints_bools import get_bool_constraints
from smt_planning.constraints_real_variables import get_variable_constraints
from smt_planning.property_links import get_property_cross_relations
from smt_planning.init import get_init
from smt_planning.goal import get_goal
from smt_planning.real_variable_contin_change import get_real_variable_continuous_changes
from smt_planning.planning_result import PlanningResult


def add_comment(solver: Solver, comment_text: str):
	# Adds a comment to the smt output in a pretty hackish way: 
	# Z3 doesn't allow adding comments, so we create a variable with the comment as its name and add it to the solver

	comment = Bool(f"## {comment_text} ##")
	solver.add(comment)

def cask_to_smt(ontology_file: str, max_happenings: int, problem_location: str, result_location:str):

	start_time = time.time()
	state_handler = StateHandler()

	# Create a Graph
	graph = Graph()
	state_handler.set_graph(graph)

	# Parse in an RDF file hosted beside this file
	graph.parse(ontology_file, format="turtle")

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
		property_dictionary = getAllProperties(happenings, event_bound)
		state_handler.set_property_dictionary(property_dictionary)

		# Get provided capabilities and transform to boolean SMT variables
		capability_dictionary = get_provided_capabilities(happenings)
		state_handler.set_capability_dictionary(capability_dictionary)

		# ------------------------Constraint Proposition (H1 + H2) --> bool properties------------------
		add_comment(solver, "Start of constraints proposition")
		bool_constraints = get_bool_constraints(happenings, event_bound)
		for bool_constraint in bool_constraints:
			solver.add(bool_constraint)	

		# ---------------------Constraint Real Variable (H5) --> real properties-----------------------------
		add_comment(solver, "Start of constraints real variables")
		variable_constraints = get_variable_constraints(happenings, event_bound)
		for variable_constraint in variable_constraints:
			solver.add(variable_constraint)	


		# ----------------- Capability Precondition ------------------------------------------------------
		add_comment(solver, "Start of preconditions")
		preconditions = getCapabilityPreconditions(happenings, event_bound)
		for precondition in preconditions:
			solver.add(precondition)

		# --------------------------------------- Capability Effect ---------------------------------------
		add_comment(solver, "Start of effects")
		effects = getCapabilityEffects(happenings, event_bound)
		for effect in effects:
			solver.add(effect)

		# Capability constraints are expressions in smt2 form that cannot be added programmatically. Thus, we take the current solver in string form
		# We create a new solver object. Then we take the current solver string and add the constraint strings. We then re-import everything back into the fresh solver object
		# It has to be a fresh object because just re-importing doesn't clear everything
		add_comment(solver, "Start of capability constraints")
		current_solver_string = solver.to_smt2()
		solver = Solver()
		constraints = getCapabilityConstraints(happenings, event_bound)
		for constraint in constraints:
			current_solver_string += f"\n{constraint}" 

		solver.from_string(current_solver_string)

		# ---------------- Constraints Capability mutexes (H14) -----------------------------------------


		# ---------------- Init  --------------------------------------------------------
		add_comment(solver, "Start of init")
		inits = get_init()
		for init in inits:
			solver.add(init)												

		# ---------------------- Goal ------------------------------------------------- 
		add_comment(solver, "Start of goal")
		goals = get_goal(happenings)
		for goal in goals:
			solver.add(goal)

		# Product Goal (aus Req Cap)

		# ------------------- Proposition support (P5 + P6) ----------------------------
		add_comment(solver, "Start of proposition support")
		proposition_supports = getPropositionSupports(happenings, event_bound)
		for support in proposition_supports:
			solver.add(support)

		# ----------------- Continuous change on real variables (P11) ------------------
		add_comment(solver, "Start of real variable continuous change")
		real_variable_cont_changes = get_real_variable_continuous_changes(happenings, event_bound)
		for real_variable_cont_change in real_variable_cont_changes:
			solver.add(real_variable_cont_change)

		# ----------------- Cross-connection of related properties (new) -----------------
		add_comment(solver, "Start of related properties")
		property_cross_relations = get_property_cross_relations(happenings, event_bound)
		for cross_relation in property_cross_relations:
			solver.add(cross_relation)

		end_time = time.time()
		print(f"Time for generating SMT: {end_time - start_time}")

		# smtlib code  
		# print(solver.to_smt2())
		with open('smtlib5.txt', 'w') as file:
			file.write(solver.to_smt2())
		

		# Check satisfiability and get the model
		solver_result = solver.check()
		end_time_solver = time.time()
		print(f"Time for solving SMT: {end_time_solver - end_time}")

		if solver_result == unsat:
			print(f"No solution with {happenings} happening(s) found.")
		else:
			model = solver.model()
			result = PlanningResult(model, problem_location, result_location)
			model_dict = {}

			for var in model:
				# print(f"{var} = {model[var]}")
				model_dict[str(var)] = str((model[var]))
			# Write the model to a JSON file
			with open('plan.json', 'w') as json_file:
				json.dump(model_dict, json_file, indent=4)
			return model 


if __name__ == '__main__': 
	ontology_file = 'ontology.ttl'
	max_happenings = 3
	problem_location = "problem.smt"
	result_location = 'plan.json'
	cask_to_smt(ontology_file, max_happenings, problem_location, result_location)
