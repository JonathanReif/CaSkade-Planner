from rdflib import Graph
from rdflib.query import ResultRow
from typing import List
from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary
from z3 import Implies, BoolRef

def getCapabilityPreconditions(graph: Graph, capabilityDictionary: CapabilityDictionary, propertyDictionary: PropertyDictionary, happenings: int, eventBound: int) -> List[BoolRef]:

	# Get all resource properties for capability precondition that has to be compared with input information property (Requirement). 
	queryString = """
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>

	SELECT ?cap ?de ?log ?val WHERE {  
		?cap a CaSk:ProvidedCapability;
			^CSS:requiresCapability ?process.
		?process VDI3682:hasInput ?input.
		?input VDI3682:isCharacterizedBy ?id.
		?id DINEN61360:Expression_Goal "Requirement";
			DINEN61360:Logic_Interpretation ?log;
			DINEN61360:Value ?val.
		?de DINEN61360:has_Instance_Description ?id.
	} 
	"""
	
	results = graph.query(queryString)
	preconditions = []
	for happening in range(happenings):
		for row in results:
			currentCap = capabilityDictionary.getCapabilityVariableByIriAndHappening(row.cap, happening)	# type: ignore
			currentProp = propertyDictionary.getPropertyVariable(row.de, 0, happening)						# type: ignore
			relation = str(row.log)																			# type: ignore
			value = str(row.val)																			# type: ignore
			match relation:
				case "<":
					precondition = Implies(currentCap, currentProp < value)
				case "<=":
					precondition = Implies(currentCap, currentProp <= value)
				case "=":
					precondition = Implies(currentCap, currentProp == value)
				case "!=":
					precondition = Implies(currentCap, currentProp != value)
				case ">=":
					precondition = Implies(currentCap, currentProp >= value)
				case ">":
					precondition = Implies(currentCap, currentProp > value)
				case _:
					raise RuntimeError("Incorrent logical relation")
			
			preconditions.append(precondition)
	return preconditions


