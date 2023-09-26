from typing import Dict, List
from z3 import Bool, BoolRef
from rdflib import URIRef
from dicts.PropertyDictionary import Property
from enum import Enum

class PropertyChange(Enum):
	NoChange = 1
	ChangeByExpression = 2
	NumericConstant = 3
	SetTrue = 4
	SetFalse = 5

class CapabilityPropertyInfluence:
	def __init__(self, property: Property, has_effect: PropertyChange):
		self.property = property
		self.has_effect= has_effect

class CapabilityOccurrence:
	def __init__(self, iri: str, happening: int):
		self.iri = iri
		self.happening = happening
		z3_variable_name = iri + "_" + str(happening)
		self.z3_variable = Bool(z3_variable_name)

class Capability:
	def __init__(self, iri: str, capability_type: str, input_properties: List[Property], output_properties: List[CapabilityPropertyInfluence]):
		self.iri = iri
		self.capability_type = capability_type
		self.input_properties = input_properties
		self.output_properties = output_properties
		self.occurrences: Dict[int, CapabilityOccurrence] = {}

	def add_occurrence(self, occurrence: CapabilityOccurrence):
		happening = occurrence.happening
		self.occurrences.setdefault(happening, occurrence)

	def add_input_property(self, property: Property):
		self.input_properties.append(property)

	def add_output_property(self, property_influence: CapabilityPropertyInfluence):
		self.output_properties.append(property_influence)


class CapabilityDictionary:
	def __init__(self):
		self.capabilities: Dict[str, Capability] = {}

	def add_capability_occurrence(self, iri: str, capability_type: str, happening: int, input_properties: List[Property], output_properties: List[CapabilityPropertyInfluence]):
		capability = Capability(iri, capability_type, input_properties, output_properties)
		self.capabilities.setdefault(iri, capability)
		capability_occurrence = CapabilityOccurrence(iri, happening)
		self.capabilities[iri].add_occurrence(capability_occurrence)

	def get_capability(self, iri:str) -> Capability:
		if (not iri in self.capabilities):
			raise KeyError(f"There is no capability with key {iri}.")
		return self.capabilities[iri]

	def get_capability_occurrence(self, iri: str, happening:int) -> CapabilityOccurrence:
		capability = self.get_capability(iri)
		return capability.occurrences[happening]