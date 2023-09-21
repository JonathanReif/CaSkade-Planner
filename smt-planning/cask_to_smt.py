import json 

from rdflib import Graph
from z3 import Solver, sat 

from variable_declaration import getProvidedCapabilities, getAllProperties
from capability_preconditions import getCapabilityPreconditions
from capability_effects import getCapabilityEffects
from capability_constraints import getCapabilityConstraints
from bool_variable_support import getPropositionSupports
from variable_constraints import get_variable_constraints
from property_links import get_related_properties
from init import get_init
from goal import get_goal
from real_variable_contin_change import get_real_variable_continuous_changes

def cask_to_smt():

	# SMT Solver
	solver = Solver()

	# Create a Graph
	g = Graph()

	# Parse in an RDF file hosted beside this file
	g.parse("order_ontology.ttl", format="turtle")

	# TODO: Happenings müssen je nach Lösung angepasst werden (for schleife) 
	happenings = 1
	# Fixed upper bound for number of events in one happening. Currently no events, so we just have the start and end of a happening
	event_bound = 2

	# ------------------------------Variable Declaration------------------------------------------ 	
	# Get all properties connected to provided capabilities as inputs or outputs
	property_dictionary = getAllProperties(g, happenings, event_bound)

	# Get provided capabilities and transform to boolean SMT variables
	capability_dictionary = getProvidedCapabilities(g, happenings, event_bound)

	# ------Constraint Proposition (H1 + H2) and Cosntraint Real Variable (H5) --> bool and real properties-------

	variable_constraints = get_variable_constraints(g, capability_dictionary, property_dictionary, happenings, event_bound)
	for constraint in variable_constraints:
		solver.add(constraint)	


	# ----------------- Capability Precondition ------------------------------------------------------
	preconditions = getCapabilityPreconditions(g, capability_dictionary, property_dictionary, happenings, event_bound)
	for precondition in preconditions:
		solver.add(precondition)

	# --------------------------------------- Capability Effect ---------------------------------------
	effects = getCapabilityEffects(g, capability_dictionary, property_dictionary, happenings, event_bound)
	for effect in effects:
		solver.add(effect)

	
	current_solver_string = solver.to_smt2()
	constraints = getCapabilityConstraints(g, capability_dictionary, property_dictionary, happenings, event_bound)
	for constraint in constraints:
		current_solver_string += f"\n{constraint}" 

	solver.from_string(current_solver_string)

	# ---------------- Constraints Capability mutexes (H14) -----------------------------------------


	# ---------------- Init  --------------------------------------------------------

	inits = get_init(g, property_dictionary)
	for init in inits:
		solver.add(init)												

	# ---------------------- Goal ------------------------------------------------- 

	goals = get_goal(g, property_dictionary, happenings)
	for goal in goals:
		solver.add(goal)

	# Product Goal (aus Req Cap)

	# ------------------- Proposition support (P5 + P6) ----------------------------
	proposition_supports = getPropositionSupports(property_dictionary, happenings, event_bound)
	for support in proposition_supports:
		solver.add(support)

	# ----------------- Continuous change on real variables (P11) ------------------

	real_variable_cont_changes = get_real_variable_continuous_changes(property_dictionary, happenings, event_bound)
	for real_variable_cont_change in real_variable_cont_changes:
		solver.add(real_variable_cont_change)

	# ----------------- Cross-connection of related properties (new) -----------------
	property_cross_relations = get_related_properties(g, property_dictionary, happenings, event_bound)
	for cross_relation in property_cross_relations:
		solver.add(cross_relation)

	# smtlib code  
	print(solver.to_smt2())

	# Check satisfiability and get the model
	if solver.check() == sat:
		model = solver.model()
		model_dict = {}

		for var in model:
			print(f"{var} = {model[var]}")
			model_dict[str(var)] = str((model[var]))
		# Write the model to a JSON file
		with open('plan.json', 'w') as json_file:
			json.dump(model_dict, json_file, indent=4)
		return model 
	else:
		print("No solution found.")

if __name__ == '__main__': 
	cask_to_smt()