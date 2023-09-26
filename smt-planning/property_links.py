
from rdflib import Graph, Variable, URIRef
from rdflib.term import Identifier 
from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary
from typing import List, MutableSequence, Mapping, Dict
from operator import itemgetter
from z3 import BoolRef, ArithRef

def get_property_cross_relations(graph: Graph, property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List[BoolRef]:
	
	related_property_pairs = PropertyPairCache.get_property_pairs(graph)
	
	relation_constraints = []

	# 1: Relate inits. We need to get inputs of the required capability and make sure related properties are bound to the values of these properties.
	# Both requirements and assurances need to be bound because otherwise assurance would be "floating" and could be set to goal without respecting caps
	required_input_properties = get_inputs_of_required_cap(graph)
	for required_input_prop_iri in required_input_properties:
		related_prop_iris = get_partners(str(required_input_prop_iri), related_property_pairs)
		for related_property_iri in related_prop_iris:
			# related_property_relation_type = property_dictionary.get_relation_type_of_property(related_property_iri)
			# if related_property_relation_type != "Input":
			# 	continue

			required_input_prop = property_dictionary.get_required_property_occurrence(str(required_input_prop_iri)).z3_variable
			try: 
				related_property = property_dictionary.get_provided_property_occurrence(str(related_property_iri), 0, 0).z3_variable
				relation_constraint = (required_input_prop == related_property)
				relation_constraints.append(relation_constraint)
			except KeyError:
				print(f"There is no provided property with key {related_property_iri}.")

	# 2: Relate goals. We need to get all outputs of the required capability and make sure that related output properties are bound to the valu of these outputs
	# Only constrain output properties because we are only interested in the final output. The input depends on the capability and must not be "over-constrained"
	required_output_properties = get_outputs_of_required_cap(graph)
	for required_output_prop_iri in required_output_properties:
		related_prop_iris = get_partners(str(required_output_prop_iri), related_property_pairs)
		for related_property_iri in related_prop_iris:
			related_property_relation_type = property_dictionary.get_property_relation_type(str(related_property_iri))
			if related_property_relation_type != "Output":
				continue

			required_output_prop = property_dictionary.get_required_property_occurrence(str(required_output_prop_iri)).z3_variable
			try:
				related_property = property_dictionary.get_provided_property_occurrence(str(related_property_iri), happenings-1, 1).z3_variable
				relation_constraint = (required_output_prop == related_property)
				relation_constraints.append(relation_constraint)
			except KeyError: 
				print(f"There is no provided property with key {related_property_iri}.")


	return relation_constraints

def get_inputs_of_required_cap(graph: Graph):
	query_string = """
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT ?cap ?input ?de WHERE {
		?cap a CaSk:RequiredCapability;
			^CSS:requiresCapability ?process.
		?process VDI3682:hasInput ?input.
		?de a DINEN61360:Data_Element.
		?de DINEN61360:has_Type_Description ?td;
			DINEN61360:has_Instance_Description ?id.
		?input VDI3682:isCharacterizedBy ?id.
	}
	"""
	
	result = graph.query(query_string)
	input_iris = [binding.get('de') for binding in result.bindings]
	return input_iris


def get_outputs_of_required_cap(graph: Graph):
	query_string = """
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT ?cap ?output ?de WHERE {
		?cap a CaSk:RequiredCapability;
			^CSS:requiresCapability ?process.
		?process VDI3682:hasOutput ?output.
		?de a DINEN61360:Data_Element.
		?de DINEN61360:has_Type_Description ?td;
			DINEN61360:has_Instance_Description ?id.
		?output VDI3682:isCharacterizedBy ?id.
	}
	"""
	
	result = graph.query(query_string)
	output_iris = [binding.get('de') for binding in result.bindings]
	return output_iris



def get_related_properties_at_same_time(graph: Graph, property_dictionary: PropertyDictionary, property_iri:str ,happening: int, event: int) -> List[ArithRef | BoolRef]:

	property_pairs = PropertyPairCache.get_property_pairs(graph)
	result_related_properties: List[ArithRef | BoolRef] = []

	# Find all related partners of the given property
	related_properties = get_partners(property_iri, property_pairs)
	
	for related_property in related_properties:
		# Get related at same happening and event, but only if Output
		# if property_dictionary.get_relation_type_of_property(related_property) != "Output": continue
		
		try: 
			related_property_same_time = property_dictionary.get_provided_property_occurrence(str(related_property), happening, event).z3_variable
			result_related_properties.append(related_property_same_time)
		except KeyError: 
			print(f"There is no provided property with key {related_property}.")

	return result_related_properties


class PropertyPair:
	def __init__(self, property_a: URIRef, property_b: URIRef) -> None:
		self.property_a = property_a
		self.property_b = property_b


def get_partners(property_iri: str, property_pairs:List[PropertyPair]) -> List[URIRef]:
	# Returns all partners of a property from the list of property pairs
	# Gets partnerA if partnerB is given and partnerB if partnerA is given
	related_properties = []
	for property_pair in property_pairs:
		if (str(property_iri) ==  str(property_pair.property_a)):
			related_properties.append(property_pair.property_b)
		if (str(property_iri) ==  str(property_pair.property_b)):
			related_properties.append(property_pair.property_a)
		
	return related_properties



def is_existing(pair: PropertyPair, other_pair: PropertyPair) -> bool:
	a_same_a = str(pair.property_a) == str(other_pair.property_a)
	b_same_b = str(pair.property_b) == str(other_pair.property_b)
	a_same_b = str(pair.property_a) == str(other_pair.property_b)
	b_same_a = str(pair.property_b) == str(other_pair.property_a)
	return (a_same_a and b_same_b) or (a_same_b and b_same_a)

def is_self_pair(pair: PropertyPair) -> bool:
	return str(pair.property_a) == str(pair.property_b)


def find_property_pairs(graph:Graph) -> List[PropertyPair]: 
	# Queries the graph and finds all implicitly related property pairs

	query_string = """
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT ?cap ?inOut ?de ?td ?inOutType ?inOutSubType WHERE {
		?cap a ?capType;
			^CSS:requiresCapability ?process.
		values ?capType { CaSk:ProvidedCapability CaSk:RequiredCapability }.
		?process VDI3682:hasInput|VDI3682:hasOutput ?inOut.
		?de a DINEN61360:Data_Element.
		?de DINEN61360:has_Type_Description ?td;
			DINEN61360:has_Instance_Description ?id.
		?inOut VDI3682:isCharacterizedBy ?id.
		BIND(VDI3682:Product AS ?inOutType)
		?inOut a ?inOutType.
		OPTIONAL {
			?inOut a ?inOutSubType.
			?inOutSubType rdfs:subClassOf VDI3682:Product.
		}
	}
	"""

	result = graph.query(query_string)
	# Creates a list of pairs of related properties, i.e. a properties with a different data_element that is still implicitly connected and thus must be linked in SMT
	# Requirement for a related property:
	# Must belong to different capability, must have same type description and either both properties dont have a product subtype or both have the same subtype
	related_property_pairs: List[PropertyPair] = []
	for binding in result.bindings:
		related_bindings = list(filter(lambda x: is_related_property_binding(binding, x), result.bindings))
		for related_binding in related_bindings:
			pair = PropertyPair(binding.get("de"), related_binding.get("de"))
			existing_pair = next(filter(lambda x: is_existing(pair, x), related_property_pairs), None)
			self_pair = is_self_pair(pair) 
			if not existing_pair and not self_pair:
				related_property_pairs.append(pair)

	return related_property_pairs

class CapabilityPair:
	def __init__(self, capability_a: URIRef, capability_b: URIRef, property: URIRef) -> None:
		self.capability_a = capability_a
		self.capability_b = capability_b
		self.property = property

def get_capability_partners(capability_iri: str, property_iri: str, capability_pairs:List[CapabilityPair]) -> List[URIRef]:
	# Returns all partners of a property from the list of property pairs
	# Gets partnerA if partnerB is given and partnerB if partnerA is given
	related_capabilities = []
	for capability_pair in capability_pairs:
		if (str(capability_iri) == str(capability_pair.capability_a)) and (str(property_iri) == str(capability_pair.property)):
			related_capabilities.append(capability_pair.capability_b)
		if (str(capability_iri) == str(capability_pair.capability_b)) and (str(property_iri) == str(capability_pair.property)):
			related_capabilities.append(capability_pair.capability_a)
		
	return related_capabilities

def is_existing_cap(pair: CapabilityPair, other_pair: CapabilityPair) -> bool:
	a_same_a = str(pair.capability_a) == str(other_pair.capability_a) and str(pair.property) == str(other_pair.property)
	b_same_b = str(pair.capability_b) == str(other_pair.capability_b) and str(pair.property) == str(other_pair.property)
	a_same_b = str(pair.capability_a) == str(other_pair.capability_b) and str(pair.property) == str(other_pair.property)
	b_same_a = str(pair.capability_b) == str(other_pair.capability_a) and str(pair.property) == str(other_pair.property)
	return (a_same_a and b_same_b) or (a_same_b and b_same_a)

def find_capability_pairs(graph: Graph) -> List[CapabilityPair]:
	query_string = """
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT ?cap ?de ?td ?inOutSubType WHERE {
		?cap a CaSk:ProvidedCapability;
			^CSS:requiresCapability ?process.
		?process VDI3682:hasInput|VDI3682:hasOutput ?inOut.
		?de a DINEN61360:Data_Element.
		?de DINEN61360:has_Type_Description ?td;
			DINEN61360:has_Instance_Description ?id.
		?inOut VDI3682:isCharacterizedBy ?id.
		BIND(VDI3682:Product AS ?inOutType)
		?inOut a ?inOutType.
		OPTIONAL {
			?inOut a ?inOutSubType.
			?inOutSubType rdfs:subClassOf VDI3682:Product.
		}
	} """

	result = graph.query(query_string)
	# Creates a list of pairs of related capabilites, i.e. a capability with a different data_element that is still implicitly connected and thus must be linked in SMT
	# Requirement for a related capability:
	# Property of Output must have same type description and either both properties dont have a product subtype or both have the same subtype
	related_capability_pairs: List[CapabilityPair] = []
	for binding in result.bindings:
		related_bindings = list(filter(lambda x: is_related_capability_binding(binding, x), result.bindings))
		for related_binding in related_bindings:
			pair = CapabilityPair(binding.get("cap"), related_binding.get("cap"), binding.get("de"))
			existing_pair = next(filter(lambda x: is_existing_cap(pair, x), related_capability_pairs), None)
			# TODO: do we need to check for same pair here as well?
			if not existing_pair:
				related_capability_pairs.append(pair)

	return related_capability_pairs

def get_related_capabilities_at_same_time(graph: Graph, capability_dictionary: CapabilityDictionary, capability_iri:str, property_iri:str, happening: int) -> List[BoolRef]:

	capability_pairs = CapabilityPairCache.get_capability_pairs(graph)
	result_related_capabilities: List[BoolRef] = []

	# Find all related partners of the given capability
	related_capabilities = get_capability_partners(capability_iri, property_iri, capability_pairs)
	
	for related_capability in related_capabilities:
		# Get related at same happening

		# query_string = """
		# 	PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
		# 	PREFIX OM: <http://openmath.org/vocab/math#>
		# 	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
		# 	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
		# 	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
		# 	SELECT ?cap ?constraint ?outputArgument ?eq WHERE {
		# 		?constraint a OM:Application, CSS:CapabilityConstraint.
		# 		BIND({ capIri } AS ?cap)
		# 		?cap ^CSS:requiresCapability ?process;
		# 			CSS:isRestrictedBy ?constraint.
		# 		?constraint OM:arguments/rdf:rest*/rdf:first* ?outputArgument.
		# 		?process VDI3682:hasOutput/VDI3682:isCharacterizedBy ?outputArgument.
		# 		?outputArgument ^DINEN61360:has_Instance_Description ?de. 
		# 		?de DINEN61360:has_Type_Description ?td. 
		# 		BIND({ propIri } AS ?prop)
		# 		?prop DINEN61360:has_Type_Description ?td. 
		# 		?constraint OM:operator ?eq.
		# 	} """
		# query_string = query_string.replace("{ capIri }", "<" + str(related_capability) + ">")
		# query_string = query_string.replace("{ propIri }", "<" + property_iri + ">")
		# result = graph.query(query_string)
		# for row in result: 
		# 	if str(row.eq) != "http://www.openmath.org/cd/relation1#eq" and str(row.inputType) != "http://www.w3id.org/hsu-aut/VDI3682#Information":			
		related_capability_same_time = capability_dictionary.get_capability_occurrence(str(related_capability), happening).z3_variable
		result_related_capabilities.append(related_capability_same_time)

	return result_related_capabilities

def get_related_capabilities_at_same_time_bool(graph: Graph, capability_dictionary: CapabilityDictionary, capability_iri:str, property_iri:str, happening: int) -> Dict[BoolRef, str]:

	query_string = """
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	select ?value where { 
		BIND({ capIri } AS ?cap)
		BIND({ propIri } AS ?relatedDe) 
		?cap ^CSS:requiresCapability ?process.
		?process VDI3682:hasOutput ?out.
		?de a DINEN61360:Data_Element.
		?de DINEN61360:has_Type_Description ?td;
			DINEN61360:has_Instance_Description ?id.
		?out VDI3682:isCharacterizedBy ?id.
		?id a DINEN61360:Boolean; 
			DINEN61360:Value ?value.
		?relatedDe DINEN61360:has_Type_Description ?td.
	}
"""

	capability_pairs = CapabilityPairCache.get_capability_pairs(graph)
	result_related_capabilities: Dict[BoolRef, str] = {}

	# Find all related partners of the given capability
	related_capabilities = get_capability_partners(capability_iri, property_iri, capability_pairs)
	
	for related_capability in related_capabilities:
		# Get related at same happening
		
		related_capability_same_time = capability_dictionary.get_capability_occurrence(str(related_capability), happening)
		cap_query_string = query_string.replace("{ capIri }", "<" + str(related_capability) + ">")
		cap_query_string = cap_query_string.replace("{ propIri }", "<" + property_iri + ">")
		results = graph.query(cap_query_string)
		for row in results: 
			related_capability_same_time_value = str(row.value)					#type: ignore
		result_related_capabilities[related_capability_same_time.z3_variable] = related_capability_same_time_value

	return result_related_capabilities


def is_related_property_binding(binding: Mapping[Variable, Identifier], other_binding: Mapping[Variable, Identifier]) -> bool:
	# Checks whether two properties are related
	return same_type_description(binding, other_binding) and subtype_matches(binding, other_binding)

def is_related_capability_binding(binding: Mapping[Variable, Identifier], other_binding: Mapping[Variable, Identifier]) -> bool:
	# Checks whether two properties are related
	return different_capability(binding, other_binding) and same_type_description(binding, other_binding) and subtype_matches(binding, other_binding)


def different_capability(binding: Mapping[Variable, Identifier], other_binding: Mapping[Variable, Identifier]) -> bool:
	# Checks wheter two result bindings belong to different capabilities
	return (str(binding.get("cap")) != str(other_binding.get("cap")))


def same_type_description(binding: Mapping[Variable, Identifier], other_binding: Mapping[Variable, Identifier]) -> bool:
	# Checks whether two result bindings refer to the same type description
	return (str(binding.get("td")) == str(other_binding.get("td")))


def subtype_matches(binding: Mapping[Variable, Identifier], other_binding: Mapping[Variable, Identifier]) -> bool:
	# Checks whether the product subtype of two result bindings is identical
	return (str(binding.get("inOutSubType")) == str(other_binding.get("inOutSubType")))

class PropertyPairCache:
	property_pairs: List[PropertyPair] = list()

	@staticmethod
	def get_property_pairs(graph: Graph):
		if not PropertyPairCache.property_pairs:
			PropertyPairCache.property_pairs = find_property_pairs(graph)			

		return PropertyPairCache.property_pairs

class CapabilityPairCache:
	capability_pairs: List[CapabilityPair] = list()

	@staticmethod
	def get_capability_pairs(graph: Graph):
		if not CapabilityPairCache.capability_pairs:
			CapabilityPairCache.capability_pairs = find_capability_pairs(graph)			

		return CapabilityPairCache.capability_pairs

