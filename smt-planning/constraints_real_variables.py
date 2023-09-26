from rdflib import Graph, URIRef
from z3 import Implies, Not, And
from typing import List

from dicts.CapabilityDictionary import CapabilityDictionary, Capability
from dicts.PropertyDictionary import PropertyDictionary
from property_links import get_related_capabilities, get_related_properties

def get_variable_constraints(graph: Graph, capability_dictionary: CapabilityDictionary, property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List:
	
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
	
	constraints = []

	properties = property_dictionary.provided_properties.values()
	for original_property in properties:
		if original_property.data_type != "http://www.hsu-ifa.de/ontologies/DINEN61360#Real": continue
		
		# Get all capabilities directly or indirectly influencing current property
		property_capability_iris = original_property.capability_iris
		capabilities = [capability_dictionary.get_capability(capabilit_iri) for capabilit_iri in property_capability_iris]
		
		related_capabilities: List[Capability] = []
		for capability_iri in property_capability_iris:
			current_cap_related_capabilities = get_related_capabilities(graph, capability_dictionary, property_dictionary, capability_iri, original_property.iri)
			related_capabilities.extend(current_cap_related_capabilities)
		
		all_capabilities = [*capabilities, *related_capabilities]
		
		# Get all properties (this one and its related ones)
		related_properties = get_related_properties(graph, property_dictionary, original_property.iri)
		all_properties = [original_property, *related_properties]

		all_capabilities_with_numeric_influence: List[Capability] = []
		for capability in all_capabilities:
			for property in all_properties:
				if capability.has_effect_on_property(property):
					all_capabilities_with_numeric_influence.append(capability)


		for happening in range(happenings):
			prop_start = original_property.occurrences[happening][0].z3_variable
			prop_end = original_property.occurrences[happening][1].z3_variable
			all_capability_variables_with_numeric_influence = [cap.occurrences[happening].z3_variable for cap in all_capabilities_with_numeric_influence]
			caps_constraint = [Not(cap) for cap in all_capability_variables_with_numeric_influence]                
			constraint = Implies(And(*caps_constraint), prop_end == prop_start)

			constraints.append(constraint)

	return constraints


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

# def capability_has_effect_on_property(graph: Graph, property_dict: PropertyDictionary, capability_iri: URIRef, property_iri: URIRef, happening: int, event: int):
# 	related_props = get_related_properties_at_same_time(graph, property_dict, property_iri, happening, event)