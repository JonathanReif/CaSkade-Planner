import json 

from rdflib import *
from z3 import *

import SparqlQueries as sq

from variable_declaration import getProvidedCapabilities, getAllProperties
from capability_preconditions import getCapabilityPreconditions

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
	eventBound = 2

	# ------------------------------Variable Declaration------------------------------------------ Aljosha 	
	# Get all properties connected to provided capabilities as inputs or outputs
	propertyDictionary = getAllProperties(g, happenings, eventBound)
	# properties = []
	# realProperties = propertyDictionary.getAllRealVariableStates()
	# boolProperties = propertyDictionary.getAllBoolVariableStates()
	# integerProperties = propertyDictionary.getAllIntVariableStates()
	# print(realProperties)
	# for propertyName in realProperties:
	# 	smtProperty = Real(propertyName)
	# 	properties.append(smtProperty)
	
	# for propertyName in propertyNames.integerProperties:
	# 	smtProperty = Int(propertyName)
	# 	properties.append(smtProperty)

	# for propertyName in propertyNames.boolProperties:
	# 	smtProperty = Bool(propertyName)
	# 	properties.append(smtProperty)


	# Get provided capabilities and transform to boolean SMT variables
	capabilityDictionary = getProvidedCapabilities(g, happenings, eventBound)

	# ----------------Constraint Proposition (H1 + H2) --> bool properties--------------------- Miguel


	# ----------------Constraint Real Variable (H5) --> real properties------------------------- Miguel

	# Capability properties influenced by effect of capability = all outputs that are no Information  
	cap_props_eff = []
	results = g.query(sparql_queries.get_sparql_cap_out_props())
	for happening in range(happenings):
		for row in results: 
			for cap in caps:
				if cap.decl().name() == str(row.cap) + "_" + str(happening):
					for cap_prop_1 in properties:
						if cap_prop_1.decl().name() == str(row.prop) + "_1_" + str(happening):
							cap_props_eff.append(cap_prop_1)
							for cap_prop_0 in properties:
								if cap_prop_0.decl().name() == str(row.prop) + "_0_" + str(happening): 
									cap_props_eff.append(cap_prop_0)
									solver.add(Implies(Not(cap), cap_prop_1 == cap_prop_0))
	# Capability properties not influenced by effect of capability 
	cap_props_not_eff = properties
	cap_props_not_eff = [prop for prop in cap_props_not_eff if prop not in cap_props_eff]
	for happening in range(happenings):
		for prop_0 in cap_props_not_eff:
			prop_0_name = prop_0.decl().name().rsplit('_', 2)
			for prop_1 in cap_props_not_eff:
				prop_1_name = prop_1.decl().name().rsplit('_', 2)
				if prop_0_name[0] == prop_1_name[0] and prop_1_name[1] > prop_0_name[1] and prop_0_name[2] == prop_1_name[2]:
					solver.add(prop_1 == prop_0)

	# Resource properties influenced by effect of capability
	res_props_eff = []  
	results = g.query(sparql_queries.get_sparql_res_prop_cap_eff())
	for happening in range(happenings):
		for row in results: 
			for cap in caps:
				if cap.decl().name() == str(row.cap) + "_" + str(happening):
					for res_prop_1 in properties:
						if res_prop_1.decl().name() == str(row.prop) + "_1_" + str(happening):
							res_props_eff.append(res_prop_1)
							for res_prop_0 in properties:
								if res_prop_0.decl().name() == str(row.prop) + "_0_" + str(happening): 
									res_props_eff.append(res_prop_0)
									solver.add(Implies(Not(cap), res_prop_1 == res_prop_0)) 
	# Resource properties not influenced by effect of capability 
	res_props_not_eff = properties
	res_props_not_eff = [prop for prop in res_props_not_eff if prop not in res_props_eff]
	for happening in range(happenings):
		for prop_0 in res_props_not_eff:
			prop_0_name = prop_0.decl().name().rsplit('_', 2)
			for prop_1 in res_props_not_eff:
				prop_1_name = prop_1.decl().name().rsplit('_', 2)
				if prop_0_name[0] == prop_1_name[0] and prop_1_name[1] > prop_0_name[1] and prop_0_name[2] == prop_1_name[2]:
					solver.add(prop_1 == prop_0)
	

	# ---------------- Constraints Capability --------------------------------------------------------

	# ----------------- Capability Precondition ------------------------------------------------------ Aljosha
	preconditions = getCapabilityPreconditions(g, capabilityDictionary, propertyDictionary, happenings, eventBound)
	for precondition in preconditions:
		solver.add(precondition)


	# solver.add(Implies(driveTo19_0, Rover7_velocity74_0_0 < 5.0))
	# solver.add(Implies(driveTo19_0, Rover7_longitude70_0_0 != RequiredLongitude_longitude74_0_0))
	# solver.add(Implies(driveTo19_0, Rover7_lattitude71_0_0 != RequiredLattitude_lattitude74_0_0))

	# ---------------------------- Capability Effect ------------------------------------------------- Aljosha

	# Effect 1. Fall Assurance mit Value ganz normal an Produkt 
	
	# Effect 2. Fall Assurance mit Value an Information, musst mit Produkt verknüpft werden.. 
	
	# Effect 3. Fall Assurance mit Value an Information, muss mit Ressource verknüpft werden... 
	
	# Effect 4. Fall Assurance ohne Value an Produkt, muss durch Cap-Constraint mit Parameter verknüpft werden
	
	# Effect 5. Fall Assurance ohne Value an Information, muss durch Cap-Constraint mit Parameter verknüpft werden UND mit Produkt verknüpft werden
	
	# Effect 6. Fall Assurance ohne Value an Information, muss durch Cap-Constraint mit Parameter verknüpft werden UND mit Ressource verknüpft werden         
	# wenn Output - assurance + information ist, dann ist damit Variable von Ressource gemeint!! 

	results = g.query(sparql_queries.get_sparql_cap_eff_res_prop())
	for happening in range(happenings):
		for row in results:
			for cap in caps:
				if cap.decl().name() == str(row.cap) + "_" + str(happening):
					for prop in res_props_eff:
						if prop.decl().name() == str(row.prop) + "_1_" + str(happening):
							for cap_prop in cap_props_not_eff:
								if cap_prop.decl().name() == str(row.id_i) + "_1_" + str(happening):
									solver.add(Implies(cap, prop == cap_prop))

	# ---------------- Constraints Capability mutexes (H14) --------------------------------------------------------


	# ---------------- Init  -------------------------------------------------------- Miguel

	# Resource Inits (aus domain)
	results = g.query(sparql_queries.get_sparql_res_init())
	for row in results:
		for prop in properties:
						if prop.decl().name() == str(row.id) + "_0_0":
							solver.add(prop == str(row.val))
	
	# Product Inits (aus Req Cap); gibt es auch Informationen??

	# ---------------------- Goal ------------------------------------------------- Miguel

	# Resource Goal (aus Req Cap); wenn Information  
	results = g.query(sparql_queries.get_sparql_res_goal())
	for row in results:
		for prop in properties:
			if prop.decl().name() == str(row.res_id) + "_1_" + str(happenings-1):
				solver.add(prop == str(row.val))

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