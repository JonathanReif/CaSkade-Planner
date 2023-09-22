from rdflib import Graph
from z3 import Implies, Not, And
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
        SELECT ?de (GROUP_CONCAT(?cap; separator=", ") as ?caps) WHERE { 
            ?cap a CaSk:ProvidedCapability;
                ^CSS:requiresCapability ?process.
            ?process VDI3682:hasOutput ?out.
            ?out VDI3682:isCharacterizedBy ?id.
            ?id ^DINEN61360:has_Instance_Description ?de;
                a DINEN61360:Real.
        }
        GROUP by ?de"""
    
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
            ?id ^DINEN61360:has_Instance_Description ?de;
                a DINEN61360:Real.
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
            caps_result = row.caps.split(', ')           # type: ignore 
            caps = []
            for cap in caps_result:                    # type: ignore
                currentCap = capability_dict.getCapabilityVariableByIriAndHappening(cap, happening) # type: ignore
                caps.append(currentCap)
            prop_start = property_dictionary.getPropertyVariable(row.de, happening, 0) # type: ignore
            prop_end = property_dictionary.getPropertyVariable(row.de, happening, 1) # type: ignore
            caps_constraint = [Not(cap) for cap in caps]                
            constraint = Implies(And(*caps_constraint), prop_end == prop_start)
            constraints.append(constraint)
            
            
    results = graph.query(query_props_not_effected) 
    for happening in range(happenings):
        for row in results:
            prop_start = property_dictionary.getPropertyVariable(row.de, happening, 0) # type: ignore
            prop_end = property_dictionary.getPropertyVariable(row.de, happening, 1) # type: ignore
            constraint = prop_end == prop_start
            constraints.append(constraint)

    return constraints