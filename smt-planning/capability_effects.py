from rdflib import Graph
from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary
from typing import List
from z3 import Implies

def getCapabilityEffects(graph: Graph, capability_dictionary: CapabilityDictionary, property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List:
	
	# Effect 1. Fall Assurance mit statischem Value

	# Get all capability outputs  
	query_string = """
	PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>

	select ?cap ?de ?prop where {  
		?cap a cask:ProvidedCapability;
			^CSS:requiresCapability ?process.
		?process VDI3682:hasOutput ?output.
		?output VDI3682:isCharacterizedBy ?id.
		?id DINEN61360:Expression_Goal "Assurance";
			DINEN61360:Logic_Interpretation ?log;
			DINEN61360:Value ?val.
		?de DINEN61360:has_Instance_Description ?id.
	} """

	results = graph.query(query_string)
	effects = []
	for happening in range(happenings):
		for row in results:
			current_capability = capability_dictionary.getCapabilityVariableByIriAndHappening(row.cap, happening)	# type: ignore
			effect_property = property_dictionary.getPropertyVariable(row.de, 1, happening)							# type: ignore
			relation = str(row.log)																					# type: ignore
			value = str(row.val)																					# type: ignore		
			match relation:
				case "<":
					effect = Implies(current_capability, effect_property < value)									# type: ignore
				case "<=":
					effect = Implies(current_capability, effect_property <= value)									# type: ignore
				case "=":
					effect = Implies(current_capability, effect_property == value)									# type: ignore
				case "!=":
					effect = Implies(current_capability, effect_property != value)									# type: ignore
				case ">=":
					effect = Implies(current_capability, effect_property >= value)									# type: ignore
				case ">":
					effect = Implies(current_capability, effect_property > value)									# type: ignore
				case _:
					raise RuntimeError("Incorrent logical relation")
			effects.append(effect)
	

	# Effect 2. Fall Assurance ohne statischen Value mit Constraint


	return effects