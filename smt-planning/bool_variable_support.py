from rdflib import Graph
from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary
from property_links import get_related_properties_at_same_time
from typing import List
from z3 import Implies, Not, Or

def getPropositionSupports(graph: Graph, property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List:
	supports = []
	for happening in range(happenings)[1:]:
		for property_item in property_dictionary.provided_properties.items():
			property_iri = property_item[0]
			property = property_item[1]
			if property.type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
				property_current_happening_start = property.states[happening][0]
				property_last_happening_end = property.states[happening-1][event_bound-1]
				
				# Track change between happenings, so that no random change is possible
				# TODO: Why do we need both implies (positive and negative)? Isn't this the same as setting start and last_end equal?
				# 1: If a property is set at start of a happening, it must have been set at the last happening's end (either same or related property)
				related_properties_last_happening_end = get_related_properties_at_same_time(graph, property_dictionary, property_iri, happening-1, event_bound-1)
				support = Implies(property_current_happening_start, Or(property_last_happening_end, *related_properties_last_happening_end))
				supports.append(support)
				
				# 1: If a property is NOT set at start of a happening, it must NOT have been set at the last happening's end (either same or related property)
				nots = [Not(x) for x in related_properties_last_happening_end]
				support_negated = Implies(Not(property_current_happening_start), Or(Not(property_last_happening_end), *nots))
				supports.append(support_negated)

	return supports
