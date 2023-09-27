from rdflib import Graph
from z3 import BoolRef, Implies, Not, Or
from typing import List

from dicts.CapabilityDictionary import CapabilityDictionary, Capability, CapabilityOccurrence
from dicts.PropertyDictionary import PropertyDictionary
from property_links import get_related_capabilities, get_related_properties

def get_bool_constraints(graph: Graph, capability_dictionary: CapabilityDictionary, property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List:
	
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
	
	constraints = []

	properties = property_dictionary.provided_properties.values()
	for original_property in properties:
		if original_property.data_type != "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean": continue

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

		all_true_setting_capabilities: List[Capability] = []
		all_false_setting_capabilities: List[Capability] = []
		for capability in all_capabilities:
			for property in all_properties:
				if capability.sets_property_true(property):
					all_true_setting_capabilities.append(capability)
				if capability.sets_property_false(property):
					all_false_setting_capabilities.append(capability)

		for happening in range(happenings):
			prop_start = original_property.occurrences[happening][0].z3_variable
			prop_end = original_property.occurrences[happening][1].z3_variable
			all_true_setting_capability_variables = [cap.occurrences[happening].z3_variable for cap in all_true_setting_capabilities]
			all_false_setting_capability_variables = [cap.occurrences[happening].z3_variable for cap in all_false_setting_capabilities]
			positive_constraint = Implies(prop_end, Or(prop_start, *all_true_setting_capability_variables))
			negative_constraint = Implies(Not(prop_end), Or(Not(prop_start), *all_false_setting_capability_variables))

			constraints.append(positive_constraint)
			constraints.append(negative_constraint)

	return constraints

	# results = graph.query(query_props_effected) 
	# constraints = []
	# for happening in range(happenings):
	# 	for row in results:
	# 		value = str(row.val)
	# 		currentCap = capability_dict.getCapabilityVariableByIriAndHappening(row.cap, happening) # type: ignore                                                   
	# 		caps_result = row.caps.split(', ')                                           
	# 		prop_start = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 0) 
	# 		prop_end = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 1) 
			
	# 		if value == "true":
	# 			positive_constraint = Implies(prop_end, Or(prop_start, currentCap))
	# 			negative_constraint = Implies(Not(prop_end), Not(prop_start))
	# 			constraints.append(positive_constraint)
	# 			constraints.append(negative_constraint)
	# 		elif value == "false":
	# 			caps_sum = caps + rel_caps_neg
	# 			negative_constraint = Implies(Not(prop_end.z3_variable), Or(Not(prop_start.z3_variable), *caps_sum))
	# 			constraints.append(negative_constraint)

	# 		if previous_property == row.de: continue                                       
	# 		if previous_value == "true":
	# 			negative_constraint = Implies(Not(previous_prop_end.z3_variable), Or(Not(previous_prop_start.z3_variable), *previous_rel_neg))
	# 			constraints.append(negative_constraint)

	# 		elif previous_value == "false":
	# 			positive_constraint = Implies(previous_prop_end.z3_variable, Or(previous_prop_start.z3_variable, *previous_rel_pos))
	# 			constraints.append(positive_constraint)
			
	# 		if i == number_of_rows:
	# 			if value == "true":
	# 				negative_constraint = Implies(Not(prop_end.z3_variable), Or(Not(prop_start.z3_variable), *rel_caps_neg))
	# 				constraints.append(negative_constraint)

	# 			elif value == "false":
	# 				positive_constraint = Implies(prop_end.z3_variable, Or(prop_start.z3_variable, *rel_caps_pos))
	# 				constraints.append(positive_constraint)

	# 		previous_property = row.de                                                    
	# 		previous_value = str(row.val)                                                
	# 		previous_prop_end = prop_end
	# 		previous_prop_start = prop_start
	# 		previous_rel_pos = rel_caps_pos
	# 		previous_rel_neg = rel_caps_neg

			

	# results = graph.query(query_props_not_effected) 
	# for happening in range(happenings):
	# 	for row in results:
	# 		rel_caps_pos = []
	# 		rel_caps_neg = []
	# 		currentCap = capability_dict.get_capability_occurrence(str(row.cap), happening).z3_variable 
	# 		if str(row.val) == "true":                                                              
	# 			rel_caps_pos.append(currentCap)
	# 		elif str(row.val) == "false":                                                           
	# 			rel_caps_neg.append(currentCap)
	# 		related_caps = get_related_capabilities_bool(graph, capability_dict, str(row.cap), str(row.de), happening) 
	# 		for related_cap in related_caps:
	# 				if related_caps[related_cap] == "true": 
	# 					rel_caps_pos.append(related_cap)
	# 				elif related_caps[related_cap] == "false": 
	# 					rel_caps_neg.append(related_cap)   
	# 		prop_start = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 0).z3_variable
	# 		prop_end = property_dictionary.get_provided_property_occurrence(str(row.de), happening, 1).z3_variable 
	# 		positive_constraint = Implies(prop_end, Or(prop_start, *rel_caps_pos))
	# 		negative_constraint = Implies(Not(prop_end), Or(Not(prop_start), *rel_caps_neg))
	# 		constraints.append(positive_constraint)
	# 		constraints.append(negative_constraint)

	# return constraints