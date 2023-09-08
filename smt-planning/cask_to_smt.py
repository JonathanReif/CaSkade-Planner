import json 

from rdflib import *
from z3 import *

import SparqlQueries as sq

from variable_declaration import getProvidedCapabilities, getAllProperties
from capability_preconditions import getCapabilityPreconditions
from real_variable_constraints import get_real_variable_constraints

def cask_to_smt():

	sparql_queries = sq.SparqlQueries()

	# SMT Solver
	solver = Solver()

	# Create a Graph
	g = Graph()

	# Parse in an RDF file hosted beside this file
	g.parse("ex_merged.ttl", format="turtle")

	# TODO: Happenings müssen je nach Lösung angepasst werden (for schleife) 
	happenings = 1
	# Fixed upper bound for number of events in one happening. Currently no events, so we just have the start and end of a happening
	event_bound = 2

	# ------------------------------Variable Declaration------------------------------------------ Aljosha 	
	# Get all properties connected to provided capabilities as inputs or outputs
	property_dictionary = getAllProperties(g, happenings, event_bound)

	# Get provided capabilities and transform to boolean SMT variables
	capability_dictionary = getProvidedCapabilities(g, happenings, event_bound)

	# ----------------Constraint Proposition (H1 + H2) --> bool properties--------------------- Miguel


	# ----------------Constraint Real Variable (H5) --> real properties------------------------- Miguel

	real_variable_constraints = get_real_variable_constraints(g, capability_dictionary, property_dictionary, happenings, event_bound)
	for constraint in real_variable_constraints:
		solver.add(constraint)	

	print(solver.to_smt2())

	# ---------------- Constraints Capability --------------------------------------------------------

	# ----------------- Capability Precondition ------------------------------------------------------ Aljosha
	preconditions = getCapabilityPreconditions(g, capability_dictionary, property_dictionary, happenings, event_bound)
	for precondition in preconditions:
		solver.add(precondition)


	# solver.add(Implies(driveTo19_0, Rover7_velocity74_0_0 < 5.0))
	# solver.add(Implies(driveTo19_0, Rover7_longitude70_0_0 != RequiredLongitude_longitude74_0_0))
	# solver.add(Implies(driveTo19_0, Rover7_lattitude71_0_0 != RequiredLattitude_lattitude74_0_0))

	# ---------------------------- Capability Effect ------------------------------------------------- Aljosha

	# Effect 1. Fall Assurance mit statischem Value
	
	# Effect 2. Fall Assurance ohne statischen Value mit Constraint

	results = g.query(sparql_queries.get_sparql_cap_eff_res_prop())
	for happening in range(happenings):
		for row in results:
			current_capability = capability_dictionary.getCapabilityVariableByIriAndHappening(row.cap, happening)	# type: ignore
			effect_property = property_dictionary.getPropertyVariable(row.prop, 1, happening)						# type: ignore
			solver.add(Implies(current_capability, effect_property == row.value))									# type: ignore

	# ---------------- Constraints Capability mutexes (H14) --------------------------------------------------------


	# ---------------- Init  -------------------------------------------------------- Miguel

	# Resource Inits (aus domain)
	results = g.query(sparql_queries.get_sparql_res_init())
	for row in results:
		property = property_dictionary.getPropertyVariable(row.id, 0, 0)				# type: ignore
		solver.add(prop == str(row.val))												# type: ignore
	
	# Product Inits (aus Req Cap); gibt es auch Informationen??

	# ---------------------- Goal ------------------------------------------------- Miguel

	# Resource Goal (aus Req Cap); wenn Information  
	results = g.query(sparql_queries.get_sparql_res_goal())
	for row in results:
		property = property_dictionary.getPropertyVariable(row.id, 1, happenings-1)		# type: ignore
		solver.add(property == str(row.val))											# type: ignore

	# Product Goal (aus Req Cap)

	# ------------------- Proposition support (P5 + P6) ---------------------------- Aljosha


	# ----------------- Continuous change on real variables (P11) ------------------ Miguel

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