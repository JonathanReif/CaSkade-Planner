from dicts.PropertyDictionary import PropertyDictionary
from typing import List
from rdflib import Graph
from z3 import Or
from property_links import get_related_properties_at_same_time

def get_real_variable_continuous_changes(graph: Graph, property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List:
	continuous_changes = []
	for happening in range(happenings)[1:]:
		for property_item in property_dictionary.provided_properties.items():
			property_iri = property_item[0]
			property = property_item[1]
			if property.type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":
				property_current_happening_start = property.states[happening][0]
				property_last_happening_end = property.states[happening-1][event_bound-1]

				if property.relation_type == "Output": 
					continuous_change = property_current_happening_start == property_last_happening_end
					continuous_changes.append(continuous_change)
					continue
				
				related_properties_last_happening_end = get_related_properties_at_same_time(graph, property_dictionary, property_iri, happening-1, event_bound-1)

				# Track change between happenings, so that no random change is possible (for both the same and related properties)
				related_equations = [property_current_happening_start == x for x in related_properties_last_happening_end]
				continuous_change = Or(property_current_happening_start == property_last_happening_end, *related_equations)
				continuous_changes.append(continuous_change)
	return continuous_changes