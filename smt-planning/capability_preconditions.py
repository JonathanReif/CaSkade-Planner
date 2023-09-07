from rdflib import Graph
from typing import List
import operator
from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary
from z3 import Implies, BoolRef

def getCapabilityPreconditions(graph: Graph, capabilityDictionary: CapabilityDictionary, propertyDictionary: PropertyDictionary, happenings: int, eventBound: int) -> List[BoolRef]:

	# Get all resource properties for capability precondition that has to be compared with input information property (Requirement). 
	queryString = """
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX VDI3682: <http://www.hsu-ifa.de/ontologies/VDI3682#>
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>

	SELECT ?cap ?log ?val ?res_id WHERE {  
		?cap a CaSk:ProvidedCapability;
			VDI3682:hasInput ?i. 
		?i a VDI3682:Information; 
		DINEN61360:has_Data_Element ?de.
		?de DINEN61360:has_Instance_Description ?id;
			DINEN61360:has_Type_Description ?type.
		?id DINEN61360:Expression_Goal "Requirement";
			DINEN61360:Logic_Interpretation ?log;
			DINEN61360:Value ?val.
		FILTER NOT EXISTS {?cap VDI3682:hasInput ?ip. 
			?ip a VDI3682:Product.} 
		?res a CSS:Resource; 
			CSS:providesCapability ?cap; 
			DINEN61360:has_Data_Element ?res_de. 
		?res_de DINEN61360:has_Instance_Description ?res_id;
				DINEN61360:has_Type_Description ?type. 
		?res_id DINEN61360:Expression_Goal "Actual_Value";
				DINEN61360:Logic_Interpretation "=". 
	} 
"""
	
	results = graph.query(queryString)
	for happening in range(happenings):
		for row in results:
			currentCap = capabilityDictionary.getCapabilityVariableByIriAndHappening(row.cap, happening)
			currentProp = propertyDictionary.getPropertyVariable(row.prop, 0, happening)
			if str(row.log) == "<=":
				precondition = Implies(currentCap, currentProp <= str(row.val))
	return []


