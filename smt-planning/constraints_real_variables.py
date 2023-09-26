from rdflib import Graph, URIRef
from z3 import Implies, Not, And
from typing import List

from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary
from property_links import get_related_capabilities_at_same_time, get_related_properties_at_same_time

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
        SELECT ?de ?cap ?state WHERE { 
            ?cap a CaSk:ProvidedCapability;
                ^CSS:requiresCapability ?process.
            ?process VDI3682:hasInput ?in.
            ?in a ?state; 
                VDI3682:isCharacterizedBy ?id.
            ?id ^DINEN61360:has_Instance_Description ?de;
                a DINEN61360:Real.
            FILTER NOT EXISTS {
                ?process VDI3682:hasOutput ?out.
                ?out VDI3682:isCharacterizedBy ?out_id.
                ?out_id ^DINEN61360:has_Instance_Description ?de.
            }
        }  """
    
    results = graph.query(query_props_effected) 
    constraints = []
    for happening in range(happenings):
        for row in results:
            caps_result = row.caps.split(', ')            
            caps = []
            for cap in caps_result:                    
                currentCap = capability_dict.get_capability_occurrence(cap, happening).z3_variable 
                caps.append(currentCap)
                related_caps = get_related_capabilities_at_same_time(graph, capability_dict, cap, str(row.de), happening) 

                for related_cap in related_caps:
                    if related_cap in caps: continue
                    caps.append(related_cap)

            prop_start = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 0).z3_variable 
            prop_end = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 1).z3_variable 
            caps_constraint = [Not(cap) for cap in caps]                
            constraint = Implies(And(*caps_constraint), prop_end == prop_start)
            constraints.append(constraint)
            
            
    results = graph.query(query_props_not_effected) 
    for happening in range(happenings):
        for row in results:
            caps = []
            if str(row.state) != "http://www.w3id.org/hsu-aut/VDI3682#Information":                     
                currentCap = capability_dict.get_capability_occurrence(str(row.cap), happening).z3_variable 
                caps.append(currentCap)
            related_caps = get_related_capabilities_at_same_time(graph, capability_dict, str(row.cap), str(row.de), happening) 
            caps.extend(related_caps)
            prop_start = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 0).z3_variable 
            prop_end = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 1).z3_variable 
            if not caps: 
                constraint = prop_end == prop_start
                constraints.append(constraint)
            else: 
                caps_constraint = [Not(cap) for cap in caps]                
                constraint = Implies(And(*caps_constraint), prop_end == prop_start)
                constraints.append(constraint)

    return constraints

def capability_has_effect_on_property(graph: Graph, property_dict: PropertyDictionary, capability_iri: URIRef, property_iri: URIRef, happening: int, event: int):
    related_props = get_related_properties_at_same_time(graph, property_dict, property_iri, happening, event)