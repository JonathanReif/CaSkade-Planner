from collections import defaultdict
from rdflib import Graph
from dicts.PropertyDictionary import PropertyDictionary
from typing import List
from z3 import Implies, Not

def getPropositionSupports(graph: Graph, property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List:
	supports = []
	
	properties = property_dictionary.provided_properties
	property_iris = set([property.iri for property in properties])

	for happening in range(happenings)[1:]:
		for property_iri in property_iris:
			property_type = property_dictionary.get_property_data_type(property_iri)
			if property_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
				# TODO: This is very computationally expensive. A dict was way better
				property_current_happening_start = property_dictionary.get_provided_property(property_iri, happening, 0).z3_variable
				property_last_happening_end =  property_dictionary.get_provided_property(property_iri, happening-1, event_bound-1).z3_variable

				# Track change between happenings, so that no random change is possible
				# TODO: Why do we need both implies (positive and negative)? Isn't this the same as setting start and last_end equal?
				# 1: If a property is set at start of a happening, it must have been set at the last happening's end 
				support = Implies(property_current_happening_start, property_last_happening_end)
				supports.append(support)
				
				# 1: If a property is NOT set at start of a happening, it must NOT have been set at the last happening's end 
				support_negated = Implies(Not(property_current_happening_start), Not(property_last_happening_end))
				supports.append(support_negated)

	return supports
