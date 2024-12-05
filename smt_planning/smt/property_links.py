from typing import List, Mapping, Dict

from rdflib import Graph, Variable
from rdflib.term import Identifier 
from z3 import BoolRef

from smt_planning.smt.StateHandler import StateHandler
from smt_planning.dicts.PropertyDictionary import Property


# Define some variables to get values from SPARQL results
TD = Variable("td")
DE = Variable("de")
CAP = Variable("cap")
FPB_SUBTYPE = Variable("fpbSubType")
FPB_TYPE = Variable("fpbType")

class PropertyPair:
	# Create a new pair with sorted properties so that we can more easily compare later
	def __init__(self, property_a: Property, property_b: Property) -> None:
		self.property_a, self.property_b = sorted([property_a, property_b])

	def __repr__(self):
		return f"({self.property_a}, {self.property_b})"

	def __eq__(self, other):
		return self.property_a == other.property_a and self.property_b == other.property_b

	def __hash__(self):
		return hash((self.property_a, self.property_b))


# Private class that should not be imported. Instead only module functions are availalble outside this module
class _PropertyPairCache:
	property_pairs: List[PropertyPair] | None = list()

	def get_property_pairs(self, required_capability_iri: str):
		if not self.property_pairs:
			self.property_pairs = self.find_property_pairs(required_capability_iri)			

		return self.property_pairs

	def get_property_cross_relations(self, happenings: int, event_bound: int, required_capability_iri: str) -> List[BoolRef]:
	
		graph = StateHandler().get_graph()
		property_dictionary = StateHandler().get_property_dictionary()
		related_property_pairs = self.get_property_pairs(required_capability_iri)
		
		relation_constraints = []

		# 1: Relate inits. We need to get inputs of the required capability and make sure related properties are bound to the values of these properties.
		# Both requirements and assurances need to be bound because otherwise assurance would be "floating" and could be set to goal without respecting caps
		for required_prop in property_dictionary.required_properties.values():
			if required_prop.relation_type != "Input":
				continue
			related_properties = self.get_partners(str(required_prop.iri), related_property_pairs)
			for related_property in related_properties:
				# related_property_relation_type = property_dictionary.get_relation_type_of_property(related_property_iri)
				# if related_property_relation_type != "Input":
				# 	continue

				required_input_prop = property_dictionary.get_required_property_occurrence(str(required_prop.iri)).z3_variable
				try: 
					related_property = property_dictionary.get_provided_property_occurrence(str(related_property.iri), 0, 0).z3_variable
					relation_constraint = (required_input_prop == related_property)
					relation_constraints.append(relation_constraint)
				except KeyError:
					print(f"There is no provided property with key {related_property.iri}.")

		# 2: Relate goals. We need to get all outputs of the required capability and make sure that related output properties are bound to the valu of these outputs
		# Only constrain output properties because we are only interested in the final output. The input depends on the capability and must not be "over-constrained"
		for required_prop in property_dictionary.required_properties.values():
			if required_prop.relation_type != "Output":
				continue
			related_properties = self.get_partners(str(required_prop.iri), related_property_pairs)
			for related_property in related_properties:
				related_property_relation_type = property_dictionary.get_property_relation_type(related_property.iri)
				if related_property_relation_type != "Output":
					continue

				required_output_prop = property_dictionary.get_required_property_occurrence(str(required_prop.iri)).z3_variable
				try:
					related_property = property_dictionary.get_provided_property_occurrence(str(related_property.iri), happenings-1, 1).z3_variable
					relation_constraint = (required_output_prop == related_property)
					relation_constraints.append(relation_constraint)
				except KeyError: 
					print(f"There is no provided property with key {related_property.iri}.")
				
		return relation_constraints

	def get_related_properties(self, property_iri:str, required_capability_iri) -> List[Property]:

		property_dictionary = StateHandler().get_property_dictionary()
		result_related_properties: List[Property] = []

		# Find all related partners of the given property
		related_properties = self.get_partners(property_iri, self.get_property_pairs(required_capability_iri))
		
		# Make sure only provided ones are returned
		for related_property in related_properties:
			try: 
				related_property = property_dictionary.get_provided_property(related_property.iri)
				result_related_properties.append(related_property)
			except KeyError:
				pass
				# print(f"There is no provided property with key {related_property.iri}.")

		return result_related_properties

	# Returns all partners of a property from a list of property pairs
	def get_partners(self, property_iri: str, property_pairs: List[PropertyPair]) -> List[Property]:
		# Gets partnerA if partnerB is given and partnerB if partnerA is given
		related_properties = []
		for property_pair in property_pairs:
			if (str(property_iri) ==  str(property_pair.property_a.iri)):
				related_properties.append(property_pair.property_b)
			if (str(property_iri) ==  str(property_pair.property_b.iri)):
				related_properties.append(property_pair.property_a)
			
		return related_properties

	def is_existing(self, pair: PropertyPair, related_property_pairs: List[PropertyPair]) -> bool:
		return (pair in related_property_pairs)

	def is_self_pair(self, pair: PropertyPair) -> bool:
		return str(pair.property_a.iri) == str(pair.property_b.iri)

	def find_property_pairs(self, required_cap_iri: str) -> List[PropertyPair]: 
		# Part 1: Queries the graph and finds all implicitly related property pairs

		query_string = """
		PREFIX DINEN61360: <http://www.w3id.org/hsu-aut/DINEN61360#>
		PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
		PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
		PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
		PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
		SELECT DISTINCT ?cap ?inOut ?de ?td ?fpbType ?fpbSubType WHERE {
			?cap a ?capType;
				^CSS:requiresCapability ?process.
			values ?capType { CaSk:ProvidedCapability CaSk:RequiredCapability }.
			# Filter to get only provided caps AND the one required that we are planning for
			FILTER(?capType = CaSk:ProvidedCapability || ?cap = <{required_cap_iri}>)
			?process VDI3682:hasInput|VDI3682:hasOutput ?inOut.
			?de a DINEN61360:Data_Element.
			?de DINEN61360:has_Type_Description ?td;
				DINEN61360:has_Instance_Description ?id.
			?inOut DINEN61360:has_Data_Element ?de.
			# Get the most specific type (the one that the inOut was declared with)
			?inOut a ?fpbSubType.
			# Get the super class that is one of the subclasses of VDI3682:State
			BIND(VDI3682:Product AS ?fpbType).
			?fpbSubType rdfs:subClassOf* ?fpbType.
		}
		"""
		query_string = query_string.replace('{required_cap_iri}', required_cap_iri)
		query_handler = StateHandler().get_query_handler()
		result = query_handler.query(query_string)
		# Creates a list of pairs of related properties, i.e. a properties with a different data_element that is still implicitly connected and thus must be linked in SMT
		# Requirement for a related property:
		# Must belong to different capability, must have same type description and either both properties dont have a product subtype or both have the same subtype
		property_dictionary = StateHandler().get_property_dictionary()
		property_pairs: List[PropertyPair] = []
		for binding in result.bindings:
			related_bindings = list(filter(lambda x: self.is_related_property_binding(binding, x), result.bindings))
			for related_binding in related_bindings:
				property_a = property_dictionary.get_property(str(binding.get(DE)))
				property_b = property_dictionary.get_property(str(related_binding.get(DE)))
				pair = PropertyPair(property_a, property_b)
				existing_pair = self.is_existing(pair, property_pairs)
				self_pair = self.is_self_pair(pair)
				if not existing_pair and not self_pair:
					property_pairs.append(pair)


		# Part 2: There can also be explicit relations. As soon as an equal constraint is defined, the properties set to be equal must also be considered 
		# to be related for all other constraints to properly work
		query_string = """
		PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
		PREFIX OM: <http://openmath.org/vocab/math#>
		PREFIX DINEN61360: <http://www.w3id.org/hsu-aut/DINEN61360#>
		select ?de_a ?de_b where { 
			?constraint a CSS:CapabilityConstraint;
					OM:operator <http://www.openmath.org/cd/relation1#eq>;
					OM:arguments (?ID_a ?ID_b) .
			?de_a DINEN61360:has_Instance_Description ?ID_a.
			?de_b DINEN61360:has_Instance_Description ?ID_b.
			# Must have the same TD
			?de_a DINEN61360:has_Type_Description ?td.
			?de_b DINEN61360:has_Type_Description ?td.
			# TODO: Properly filter out constants
			FILTER(!CONTAINS(STR(?de_a), "Module_StationID"))
			FILTER(!CONTAINS(STR(?de_b), "Module_StationID"))
			FILTER(!CONTAINS(STR(?de_a), "Slide"))
			FILTER(!CONTAINS(STR(?de_b), "Slide"))
		}
		"""
		query_handler = StateHandler().get_query_handler()
		result = query_handler.query(query_string)
		DE_A = Variable("de_a")
		DE_B = Variable("de_b")
		for binding in result.bindings:
			property_a = property_dictionary.get_property(str(binding.get(DE_A)))
			property_b = property_dictionary.get_property(str(binding.get(DE_B)))
			pair = PropertyPair(property_a, property_b)
			existing_pair = self.is_existing(pair, property_pairs)
			self_pair = self.is_self_pair(pair)
			if not existing_pair and not self_pair:
				property_pairs.append(pair)

			# We also need to take into account all pairs that already existed for A and B
			partners_of_a = self.get_partners(str(binding.get(DE_A)), property_pairs)
			for partner_of_a in partners_of_a:
				is_required_prop = (partner_of_a.iri in property_dictionary.required_properties.keys())
				if is_required_prop:
					continue
				pair = PropertyPair(partner_of_a, property_b)
				existing_pair = self.is_existing(pair, property_pairs)
				self_pair = self.is_self_pair(pair)
				different_caps = set(pair.property_a.capability_iris).isdisjoint(property_b.capability_iris)
				if not existing_pair and not self_pair and different_caps:
					property_pairs.append(pair)
			
			partners_of_b = self.get_partners(str(binding.get(DE_B)), property_pairs)
			for partner_of_b in partners_of_b:
				is_required_prop = (partner_of_b.iri in property_dictionary.required_properties.keys())
				if is_required_prop:
					continue
				pair = PropertyPair(partner_of_b, property_a)
				existing_pair = self.is_existing(pair, property_pairs)
				self_pair = self.is_self_pair(pair)
				different_caps = set(pair.property_a.capability_iris).isdisjoint(property_b.capability_iris)
				if not existing_pair and not self_pair and different_caps:
					property_pairs.append(pair)

		# Resolve transitive relations: If Prop A and B are pairs and B and C are pairs, then A and C must also be pairs
		new_pairs_added = True

		while new_pairs_added:
			new_pairs_added = False
			current_pairs = property_pairs  # Copy the set to allow for iteration

			for pair1 in current_pairs:
				for pair2 in current_pairs:
					prop_1_a_is_required_prop = (pair1.property_a.iri in property_dictionary.required_properties.keys())
					prop_1_b_is_required_prop = (pair1.property_b.iri in property_dictionary.required_properties.keys())
					prop_2_a_is_required_prop = (pair2.property_a.iri in property_dictionary.required_properties.keys())
					prop_2_b_is_required_prop = (pair2.property_b.iri in property_dictionary.required_properties.keys())
					if prop_1_a_is_required_prop or prop_1_b_is_required_prop or prop_2_a_is_required_prop or prop_2_b_is_required_prop:
						continue

					# Check if pairs are transitively connected. Note that connecting elements can be first or second element, hence the need for this weird comparison
					if pair1.property_b == pair2.property_a:
						new_pair = PropertyPair(pair1.property_a, pair2.property_b)
					elif pair1.property_b == pair2.property_b:
						new_pair = PropertyPair(pair1.property_a, pair2.property_a)
					elif pair1.property_a == pair2.property_a:
						new_pair = PropertyPair(pair1.property_b, pair2.property_b)
					elif pair1.property_a == pair2.property_b:
						new_pair = PropertyPair(pair1.property_b, pair2.property_a)
					else:
						continue  # Keine transitive Verbindung gefunden, nächstes Paar

					# Nur hinzufügen, wenn das neue Pair noch nicht existiert
					existing_pair = self.is_existing(new_pair, property_pairs)
					self_pair = self.is_self_pair(new_pair)
					if not existing_pair and not self_pair:
						property_pairs.append(new_pair)
						new_pairs_added = True

		return property_pairs

	def is_related_property_binding(self, binding: Mapping[Variable, Identifier], other_binding: Mapping[Variable, Identifier]) -> bool:
		# Checks whether two properties are related.
		# a) They have to have the same type description. This is the most basic requirement as obviously, we don't want to compare length with weight etc.
		same_type = self.same_type_description(binding, other_binding)
		if not same_type: return False
		
		# b1) They have to belong to different capabilities.
		different_cap = self.different_capability(str(binding.get(CAP)), str(other_binding.get(CAP)))

		# b2) Or they have to belong to the same capability, but there must not be a explicit relation
		same_cap = not different_cap
		no_relation_in_same_cap = not self.relation_in_same_cap(binding, other_binding)

		# c1) They either have to have the same subtype. We then can assume that properties of a should be related to the props of b
		subtype_match = self.subtype_matches(binding, other_binding)

		# c2) Or one of both is a VDI3682:Product. We assume that abstract products take all properties
		one_is_abstract = self.one_is_abstract_product(binding, other_binding)

		return (different_cap or (same_cap and no_relation_in_same_cap)) and same_type and (subtype_match or one_is_abstract)
		# return different_cap and same_type and (subtype_match or one_is_abstract)

	def different_capability(self, cap_iri: str, other_cap_iri: str) -> bool:
		# Checks wheter two result bindings belong to different capabilities
		return (cap_iri != other_cap_iri)

	def relation_in_same_cap(self, binding: Mapping[Variable, Identifier], other_binding: Mapping[Variable, Identifier]) -> bool:
		# TODO: Add proper check. Currently just for testing purposes. 
		opt_a = (str(binding.get(DE) == 'http://www.hsu-hh.de/aut/ontologies/lab/MPS500/Transport#ProductAtTargetStation_StationID_DE') and str(other_binding.get(DE)) == 'http://www.hsu-hh.de/aut/ontologies/lab/MPS500/Transport#ProductAtStartStation_StationID_DE')
		opt_b = (str(other_binding.get(DE) == 'http://www.hsu-hh.de/aut/ontologies/lab/MPS500/Transport#ProductAtTargetStation_StationID_DE') and str(binding.get(DE)) == 'http://www.hsu-hh.de/aut/ontologies/lab/MPS500/Transport#ProductAtStartStation_StationID_DE')
		# if (opt_a or opt_b):
		# 	return False
		return True

	def same_type_description(self, binding: Mapping[Variable, Identifier], other_binding: Mapping[Variable, Identifier]) -> bool:
		# Checks whether two result bindings refer to the same type description
		return (str(binding.get(TD)) == str(other_binding.get(TD)))


	def subtype_matches(self, binding: Mapping[Variable, Identifier], other_binding: Mapping[Variable, Identifier]) -> bool:
		# Checks whether the product subtype of two result bindings is identical
		return (str(binding.get(FPB_SUBTYPE)) == str(other_binding.get(FPB_SUBTYPE)))

	def one_is_abstract_product(self, binding: Mapping[Variable, Identifier], other_binding: Mapping[Variable, Identifier]) -> bool:
		# One is only an abstract product (no subtype) if the subtype is defined as product
		a_is_abstract_product = str(binding.get(FPB_SUBTYPE)) == 'http://www.w3id.org/hsu-aut/VDI3682#Product'
		b_is_abstract_product = str(other_binding.get(FPB_SUBTYPE))== 'http://www.w3id.org/hsu-aut/VDI3682#Product'
		one_is_abstract_product = a_is_abstract_product or b_is_abstract_product
		return one_is_abstract_product

	def reset(self):
		self.property_pairs = None


# Create one module-wide instance
property_pair_cache = _PropertyPairCache()

def get_related_properties(property_iri: str, required_capability_iri: str) -> List[Property]:
	return property_pair_cache.get_related_properties(property_iri, required_capability_iri)

def get_property_cross_relations(happenings: int, event_bound: int, required_capability_iri: str):
	return property_pair_cache.get_property_cross_relations(happenings, event_bound, required_capability_iri)
