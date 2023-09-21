
from rdflib import Graph, Variable, URIRef
from rdflib.term import Identifier 
from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary
from typing import List, MutableSequence, Mapping
from operator import itemgetter
from z3 import BoolRef

def get_related_properties(graph: Graph, property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List[BoolRef]:
	query_string = """
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT ?cap ?de ?td ?inOutType WHERE {
		?cap a ?capType;
			^CSS:requiresCapability ?process.
		values ?capType { CaSk:ProvidedCapability CaSk:RequiredCapability }.
		?process VDI3682:hasInput|VDI3682:hasOutput ?inOut.
		?de a DINEN61360:Data_Element.
		?de DINEN61360:has_Type_Description ?td;
			DINEN61360:has_Instance_Description ?id.
		?inOut VDI3682:isCharacterizedBy ?id.
		OPTIONAL {
			?inOut a ?inOutType.
			?inOutType rdfs:subClassOf VDI3682:Product.
		}
	}
	"""

	result = graph.query(query_string)
	related_property_pairs = find_related_properties(result.bindings)

	relation_constraints = []
	for happening in range(happenings):
		for event in range(event_bound):
			for pair in related_property_pairs:
				property_a = property_dictionary.getPropertyVariable(pair.property_a, happening, event)
				property_b = property_dictionary.getPropertyVariable(pair.property_b, happening, event)
				relation_constraint = (property_a == property_b)
				relation_constraints.append(relation_constraint)

	return relation_constraints


class PropertyPair:
	def __init__(self, property_a: URIRef, property_b: URIRef) -> None:
		self.property_a = property_a
		self.property_b = property_b


def is_existing(pair: PropertyPair, other_pair: PropertyPair) -> bool:
	a_same_a = str(pair.property_a) == str(other_pair.property_a)
	b_same_b = str(pair.property_b) == str(other_pair.property_b)
	a_same_b = str(pair.property_a) == str(other_pair.property_b)
	b_same_a = str(pair.property_b) == str(other_pair.property_a)
	return (a_same_a and b_same_b) or (a_same_b and b_same_a)

def find_related_properties(result_bindings: MutableSequence[Mapping[Variable, Identifier]]) -> List[PropertyPair]: 
	# Finds a related property, i.e. a property with a different data_element that is still implicitly connected and thus must be linked in SMT
	# Requirement for a related property:
	# Must belong to different capability, must have same type description and either both properties dont have a product subtype or both have the same subtype
	# TODO: This algorithm currently finds every relation twice (A -> B, B -> A). Should be sorted out
	related_property_pairs: List[PropertyPair] = []
	for binding in result_bindings:
		related_bindings = list(filter(lambda x: is_related(binding, x), result_bindings))
		for related_binding in related_bindings:
			pair = PropertyPair(binding.get("de"), related_binding.get("de"))
			existing_pair = next(filter(lambda x: is_existing(pair, x), related_property_pairs), None)
			if not existing_pair:
				related_property_pairs.append(pair)

	return related_property_pairs

def is_related(b1: Mapping[Variable, Identifier], binding: Mapping[Variable, Identifier]) -> bool:
	return different_capability(b1.get("cap"), binding) and same_type_description(b1.get("td"), binding) and subtype_matches(b1.get("in_out_type"), binding)

def different_capability(capability_iri: Identifier, binding: Mapping[Variable, Identifier]) -> bool:
	return (str(capability_iri) != str(binding.get("cap")))

def same_type_description(type_description: Identifier, binding: Mapping[Variable, Identifier]) -> bool:
	return (str(type_description) == str(binding.get("td")))

def subtype_matches(subtype: Identifier, binding: Mapping[Variable, Identifier]) -> bool:
	return (str(subtype) == str(binding.get("in_out_type")))

