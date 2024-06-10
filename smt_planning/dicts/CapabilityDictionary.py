from typing import Dict, List
from z3 import Bool, AstRef
from smt_planning.dicts.PropertyDictionary import Property
from enum import Enum

class PropertyChange(Enum):
	NoChange = 1
	ChangeByExpression = 2
	NumericConstant = 3
	SetTrue = 4
	SetFalse = 5

class CapabilityPropertyInfluence:
	def __init__(self, property: Property, effect: PropertyChange):
		self.property = property
		self.effect = effect

class CapabilityOccurrence:
	def __init__(self, iri: str, happening: int):
		self.iri = iri
		self.happening = happening
		z3_variable_name = iri + "_" + str(happening)
		self.z3_variable = Bool(z3_variable_name)

'''
capabiltiy_type: The type of the capability, e.g., CaSk:ProvidedCapability (TODO do we need type?)
input_properties: The properties that are required for the capability to be executed
'''
class Capability:
	def __init__(self, iri: str, capability_type: str, input_properties: List[Property], output_properties: List[CapabilityPropertyInfluence], resource: str):
		self.iri = iri
		self.capability_type = capability_type
		self.input_properties = input_properties
		self.output_properties = output_properties
		self.occurrences: Dict[int, CapabilityOccurrence] = {}
		self.resource = resource

	def add_occurrence(self, occurrence: CapabilityOccurrence):
		happening = occurrence.happening
		self.occurrences.setdefault(happening, occurrence)

	def add_input_property(self, property: Property):
		self.input_properties.append(property)

	def add_output_property(self, property_influence: CapabilityPropertyInfluence):
		self.output_properties.append(property_influence)

	def has_effect_on_property(self, property: Property) -> bool:
		# Get output of this property and see if it has an effect
		outputs = [influence for influence in self.output_properties if influence.property.iri == property.iri]
		if len(outputs) == 0: return False
		return (not outputs[0].effect == PropertyChange.NoChange)

	def sets_property_true(self, property: Property) -> bool:
		outputs = [influence for influence in self.output_properties if influence.property.iri == property.iri]
		if len(outputs) == 0: return False
		return (outputs[0].effect == PropertyChange.SetTrue)
	
	def sets_property_false(self, property: Property) -> bool:
		outputs = [influence for influence in self.output_properties if influence.property.iri == property.iri]
		if len(outputs) == 0: return False
		return (outputs[0].effect == PropertyChange.SetFalse)
	
	def get_occurrence_by_z3_variable(self, z3_variable_name: str) -> CapabilityOccurrence | None:
		# Filters occurrences for the given z3_variable. There should only be one result
		for occurrence in self.occurrences.values():
			if str(occurrence.z3_variable) == z3_variable_name:
				return occurrence
		
		return None

class ConstraintInfo():
	def __init__(self, cap: str, constraintIri: str):
		self.cap = cap
		self.constraintIri = constraintIri

class CapabilityDictionary:
	def __init__(self):
		self.capabilities: Dict[str, Capability] = {}
		self.input_capability_constraints: List[ConstraintInfo] = []
		self.output_capability_constraints: List[ConstraintInfo] = []

	def add_capability(self, iri: str, capability_type: str, input_properties: List[Property], output_properties: List[CapabilityPropertyInfluence], resource:str) -> None:
		capability = Capability(iri, capability_type, input_properties, output_properties, resource)
		self.capabilities.setdefault(iri, capability)

	def add_capability_occurrences(self, happenings: int) -> None:
		for capability in self.capabilities.values():
			for happening in range(happenings):
				capability_occurrence = CapabilityOccurrence(capability.iri, happening)
				capability.add_occurrence(capability_occurrence)

	def get_capability(self, iri:str) -> Capability:
		if (not iri in self.capabilities):
			raise KeyError(f"There is no capability with key {iri}.")
		return self.capabilities[iri]

	def get_capability_occurrence(self, iri: str, happening:int) -> CapabilityOccurrence:
		capability = self.get_capability(iri)
		return capability.occurrences[happening]
	
	def get_capability_from_z3_variable(self, z3_variable: AstRef) -> CapabilityOccurrence:
		for capability in self.capabilities.values():
			capability_occurrence = capability.get_occurrence_by_z3_variable(str(z3_variable))
			if capability_occurrence is not None:
				return capability_occurrence
			
		raise KeyError(f"There is not a single capability occurrence for the z3_variable {z3_variable}")
	
	def add_capability_constraint(self, cap: str, constraintIri: str, input: bool = False) -> None:
		if input: 
			self.input_capability_constraints.append(ConstraintInfo(cap, constraintIri))
		else: 
			self.output_capability_constraints.append(ConstraintInfo(cap, constraintIri))

	def set_input_capability_constraints(self, input_constraints: List[ConstraintInfo]) -> None:
		self.input_capability_constraints = input_constraints
		
	def set_output_capability_constraints(self, output_constraints: List[ConstraintInfo]) -> None:
		self.output_capability_constraints = output_constraints