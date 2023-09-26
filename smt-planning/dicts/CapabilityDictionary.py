from typing import Dict, List
from z3 import Bool, BoolRef
from rdflib import URIRef
from dicts.PropertyDictionary import PropertyOccurrence
from enum import Enum

class PropertyChange(Enum):
	NoChange = 1
	NumericExpression = 2
	NumericConstant = 3
	SetTrue = 4
	SetFalse = 5

class PropertyInfluence:
	def __init__(self, property: PropertyOccurrence, has_effect: PropertyChange):
		self.property = property
		self.has_effect= has_effect

class CapabilityOccurrence:
	def __init__(self, iri: str, capability_type: str, happening: int, input_properties: List[PropertyOccurrence], output_properties: List[PropertyInfluence]):
		self.iri = iri
		self.happening = happening
		self.capability_type = capability_type
		self.input_properties = input_properties
		self.output_properties = output_properties
		z3_variable_name = iri + "_" + str(happening)
		self.z3_variable = Bool(z3_variable_name)


class CapabilityDictionary:
	def __init__(self):
		self.capabilities: List[CapabilityOccurrence] = []

	def add_CapabilityOccurrence(self, iri: str, capability_type: str, happening: int, input_properties: List[PropertyOccurrence], output_properties: List[PropertyInfluence]):
		capability_occurrence = CapabilityOccurrence(iri, capability_type, happening, input_properties, output_properties)
		self.capabilities.append(capability_occurrence)

	def get_capability_occurrence(self, iri: str, happening:int) -> CapabilityOccurrence:
		selected_capabilities = [cap for cap in self.capabilities if ((cap.iri == iri) and (cap.happening == happening))]
		if (len(selected_capabilities) == 0):
			raise KeyError(f"There is no capability with key {iri}.")
		if (len(selected_capabilities) > 1):
			raise KeyError(f"Multiple capabilities with IRI '{iri}' and at happening {happening}.")
		return selected_capabilities[0]