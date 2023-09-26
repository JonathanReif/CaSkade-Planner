from rdflib import Graph
from z3 import BoolRef, Implies, Not, Or
from typing import List

from dicts.CapabilityDictionary import CapabilityDictionary, CapabilityOccurrence
from dicts.PropertyDictionary import PropertyDictionary
from property_links import get_related_capabilities_at_same_time_bool

def get_bool_constraints(graph: Graph, capability_dict: CapabilityDictionary, property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List:
    
    # get all properties influenced by capability effect
    query_props_effected = """
    PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
    PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
    PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
    PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?de ?val (GROUP_CONCAT(?cap; separator=", ") as ?caps) WHERE { 
        ?cap a CaSk:ProvidedCapability;
            ^CSS:requiresCapability ?process.
        ?process VDI3682:hasOutput ?out.
        ?out VDI3682:isCharacterizedBy ?id.
        ?id ^DINEN61360:has_Instance_Description ?de;
            a DINEN61360:Boolean; 
            DINEN61360:Value ?val. 
    }
    GROUP by ?de ?val """
    
    # get all properties that are not influenced by capability effect
    query_props_not_effected = """
        PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
        PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
        PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
        PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?de ?cap ?val WHERE { 
            ?cap a CaSk:ProvidedCapability;
                ^CSS:requiresCapability ?process.
            ?process VDI3682:hasInput ?in.
            ?in VDI3682:isCharacterizedBy ?id.
            ?id ^DINEN61360:has_Instance_Description ?de;
                a DINEN61360:Boolean. 
            ?de DINEN61360:has_Type_Description ?td. 
            ?process VDI3682:hasOutput ?out.
            ?out VDI3682:isCharacterizedBy ?out_id.
            ?out_id ^DINEN61360:has_Instance_Description ?out_de;
                a DINEN61360:Boolean;
                DINEN61360:Value ?val. 
            ?out_de DINEN61360:has_Type_Description ?td. 
            FILTER NOT EXISTS {
                ?process VDI3682:hasOutput ?out2.
                ?out2 VDI3682:isCharacterizedBy ?out2_id.
                ?out2_id ^DINEN61360:has_Instance_Description ?de.
            }
        } """
	
    results = graph.query(query_props_effected) 
    constraints = []
    for happening in range(happenings):
        previous_property = None
        previous_value = None
        previous_prop_start = None
        previous_prop_end = None
        previous_rel_pos = []
        previous_rel_neg = []
        i = 0
        number_of_rows = len(results)
        for row in results:
            i += 1
            value = str(row.val)                                                        
            caps_result = row.caps.split(', ')                                           
            caps: List[BoolRef] = []
            rel_caps_pos = []
            rel_caps_neg = []
            for cap in caps_result:                                                     
                currentCap = capability_dict.get_capability_occurrence(cap, happening) 
                caps.append(currentCap.z3_variable)
                related_caps = get_related_capabilities_at_same_time_bool(graph, capability_dict, cap, str(row.de), happening) 
                for related_cap in related_caps:
                    if related_cap in caps or related_caps[related_cap] == "true": 
                        rel_caps_pos.append(related_cap)
                    elif related_cap in caps or related_caps[related_cap] == "false": 
                        rel_caps_neg.append(related_cap)   
                
            prop_start = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 0) 
            prop_end = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 1) 
            
            if value == "true":
                caps_sum = caps + rel_caps_pos
                constraint_1 = Implies(prop_end.z3_variable, Or(prop_start.z3_variable, *caps_sum))
                constraints.append(constraint_1)
            elif value == "false":
                caps_sum = caps + rel_caps_neg
                constraint_2 = Implies(Not(prop_end.z3_variable), Or(Not(prop_start.z3_variable), *caps_sum))
                constraints.append(constraint_2)

            if previous_property == row.de: continue                                       
            if previous_value == "true":
                constraint_2 = Implies(Not(previous_prop_end.z3_variable), Or(Not(previous_prop_start.z3_variable), *previous_rel_neg))
                constraints.append(constraint_2)

            elif previous_value == "false":
                constraint_1 = Implies(previous_prop_end.z3_variable, Or(previous_prop_start.z3_variable, *previous_rel_pos))
                constraints.append(constraint_1)
            
            if i == number_of_rows:
                if value == "true":
                    constraint_2 = Implies(Not(prop_end.z3_variable), Or(Not(prop_start.z3_variable), *rel_caps_neg))
                    constraints.append(constraint_2)

                elif value == "false":
                    constraint_1 = Implies(prop_end.z3_variable, Or(prop_start.z3_variable, *rel_caps_pos))
                    constraints.append(constraint_1)

            previous_property = row.de                                                    
            previous_value = str(row.val)                                                
            previous_prop_end = prop_end
            previous_prop_start = prop_start
            previous_rel_pos = rel_caps_pos
            previous_rel_neg = rel_caps_neg

            

    results = graph.query(query_props_not_effected) 
    for happening in range(happenings):
        for row in results:
            rel_caps_pos = []
            rel_caps_neg = []
            currentCap = capability_dict.get_capability_occurrence(str(row.cap), happening).z3_variable 
            if str(row.val) == "true":                                                              
                rel_caps_pos.append(currentCap)
            elif str(row.val) == "false":                                                           
                rel_caps_neg.append(currentCap)
            related_caps = get_related_capabilities_at_same_time_bool(graph, capability_dict, str(row.cap), str(row.de), happening) 
            for related_cap in related_caps:
                    if related_caps[related_cap] == "true": 
                        rel_caps_pos.append(related_cap)
                    elif related_caps[related_cap] == "false": 
                        rel_caps_neg.append(related_cap)   
            prop_start = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 0).z3_variable
            prop_end = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 1).z3_variable 
            constraint_1 = Implies(prop_end, Or(prop_start, *rel_caps_pos))
            constraint_2 = Implies(Not(prop_end), Or(Not(prop_start), *rel_caps_neg))
            constraints.append(constraint_1)
            constraints.append(constraint_2)

    return constraints