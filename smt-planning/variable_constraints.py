from rdflib import Graph
from z3 import Implies, Not
from typing import List

from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary

def get_variable_constraints(graph: Graph, capability_dict: CapabilityDictionary, property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List:
    
    # get all properties influenced by capability effect
    query_props_effected = """
        PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
        PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
        PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
        PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
        SELECT ?cap ?de WHERE { 
            ?cap a CaSk:ProvidedCapability;
                ^CSS:requiresCapability ?process.
            ?process VDI3682:hasOutput ?out.
            ?out VDI3682:isCharacterizedBy ?id.
            ?id ^DINEN61360:has_Instance_Description ?de.
        } """
    
    # get all properties that are not influenced by capability effect
    query_props_not_effected = """
        PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
        PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
        PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
        PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
        SELECT ?de WHERE { 
            ?cap a CaSk:ProvidedCapability;
                ^CSS:requiresCapability ?process.
            ?process VDI3682:hasInput ?in.
            ?in VDI3682:isCharacterizedBy ?id.
            ?id ^DINEN61360:has_Instance_Description ?de.
            FILTER NOT EXISTS {
                ?process VDI3682:hasOutput ?out.
                ?out VDI3682:isCharacterizedBy ?out_id.
                ?out_id ^DINEN61360:has_Instance_Description ?de.
            }
        } """
	
    results = graph.query(query_props_effected) 
    constraints = []
    for happening in range(happenings):
        for row in results:
            currentCap = capability_dict.getCapabilityVariableByIriAndHappening(row.cap, happening) # type: ignore
            prop_start = property_dictionary.getPropertyVariable(row.de, 0, happening) # type: ignore
            prop_end = property_dictionary.getPropertyVariable(row.de, 1, happening) # type: ignore
            prop_type = property_dictionary.getPropertyType(row.de) # type: ignore
            if prop_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":
                constraint = Implies(Not(currentCap), prop_end == prop_start)
                constraints.append(constraint)
            if prop_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
                constraint_1 = Implies(currentCap, prop_end == prop_start)
                constraint_2 = Implies(Not(currentCap), Not(prop_end) == Not(prop_start))
                constraints.append(constraint_1)
                constraints.append(constraint_2)
            
    results = graph.query(query_props_not_effected) 
    for happening in range(happenings):
        for row in results:
            prop_start = property_dictionary.getPropertyVariable(row.de, 0, happening) # type: ignore
            prop_end = property_dictionary.getPropertyVariable(row.de, 1, happening) # type: ignore
            prop_type = property_dictionary.getPropertyType(row.de) # type: ignore
            if prop_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":
                constraint = prop_end == prop_start
                constraints.append(constraint)
            if prop_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
                constraint_1 = Implies(prop_end, prop_start)
                constraint_2 = Implies(Not(prop_end), Not(prop_start))
                constraints.append(constraint_1)
                constraints.append(constraint_2)

    return constraints