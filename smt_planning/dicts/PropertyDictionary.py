from typing import Dict, Set, List
from z3 import Real, Bool, Int, AstRef
from enum import Enum

# data_type is some instance of http://www.hsu-ifa.de/ontologies/DINEN61360#Simple_Data_Type
class PropertyOccurrence:
	def __init__(self, iri: str, data_type: str, happening: int, event: int):
		self.iri = iri
		self.happening = happening
		self.event = event
		z3_variable_name = iri + "_" + str(happening) + "_" + str(event)
		match data_type:
			case "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":
				self.z3_variable = Real(z3_variable_name)
			case "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
				self.z3_variable = Bool(z3_variable_name)
			case "http://www.hsu-ifa.de/ontologies/DINEN61360#Integer":
				self.z3_variable = Int(z3_variable_name)
			case _  :
				# Base case if no type given: Create a real
				self.z3_variable = Real(z3_variable_name)

'''
iri is the IRI of the data element
data_type is some instance of http://www.hsu-ifa.de/ontologies/DINEN61360#Simple_Data_Type
relation_type is the relation type of the property, i.e., "hasInput" or "hasOutput"
'''
class Property:
	def __init__(self, iri: str, data_type: str, relation_type: str, capability_iris: Set[str]):
		self.iri = iri
		self.data_type = data_type
		self.relation_type = relation_type
		self.capability_iris = capability_iris
		self.occurrences: Dict[int, Dict[int, PropertyOccurrence]] = {}

	def add_occurrence(self, occurrence: PropertyOccurrence):
		happening = occurrence.happening
		event = occurrence.event
		self.occurrences.setdefault(happening, {}).setdefault(event, occurrence)

	def get_occurrence_by_z3_variable(self, z3_variable_name: str) -> PropertyOccurrence | None:
		# Filters occurrences for the given z3_variable. There should only be one result
		happening_occurrences = [occ for occ in self.occurrences.values()]
		all_occurrences_2d = [list(occ.values()) for occ in happening_occurrences]
		all_occurrences: List[PropertyOccurrence] = []
		[all_occurrences.extend(occ) for occ in all_occurrences_2d]
		try:
			occurrence = [occurrence for occurrence in all_occurrences if str(occurrence.z3_variable) == z3_variable_name][0]
			return occurrence
		except:
			return None
		
class CapabilityType(Enum):
	ProvidedCapability = 1
	RequiredCapability = 2

class InstanceDescription:
	def __init__(self, iri: str, cap_iri: str, expr_goal: str, logical_interpretation: str, value: str):
		self.iri = iri
		self.cap_iri = cap_iri
		self.expr_goal = expr_goal
		self.logical_interpretation = logical_interpretation
		self.value = value

# InstanceDescription of a DataElement with DINEN61360:Expression_Goal "Requirement"
class Precondition(InstanceDescription):
	def __init__(self, iri: str, cap_iri: str, logical_interpretation: str, value: str) -> None:
		super().__init__(iri, cap_iri, "Requirement", logical_interpretation, value)

# InstanceDescription of a DataElement with DINEN61360:Expression_Goal "Assurance"
class Effect(InstanceDescription):
	def __init__(self, iri: str, cap_iri: str, logical_interpretation: str, value: str) -> None:
		super().__init__(iri, cap_iri, "Assurance", logical_interpretation, value)

class Init(InstanceDescription):
	def __init__(self, iri: str, cap_iri: str, logical_interpretation: str, value: str) -> None:
		super().__init__(iri, cap_iri, "Actual_Value", logical_interpretation, value)

class Goal(InstanceDescription):
	def __init__(self, iri: str, cap_iri: str, logical_interpretation: str, value: str) -> None:
		super().__init__(iri, cap_iri, "Requirement", logical_interpretation, value)

class PropertyDictionary:
	def __init__(self):
		self.provided_properties: Dict[str, Property] = {}
		self.required_properties: Dict[str, Property] = {}
		self.preconditions: Dict[str, Precondition] = {}
		self.effects: Dict[str, Effect] = {}
		self.inits: Dict[str, Init] = {}
		self.goals: Dict[str, Goal] = {}

	def add_provided_property(self, iri: str, data_type: str, relation_type: str, capability_iris: Set[str], expression_goal: str = "", logical_interpretation: str = "", value: str = ""):
		property = Property(iri, data_type, relation_type, capability_iris)
		self.provided_properties.setdefault(iri, property)

	def add_property_occurrences(self, happenings: int, event_bound: int) -> None:
		for property in self.provided_properties.values():
			for happening in range(happenings):
				for event in range(event_bound):
					property_occurrence = PropertyOccurrence(property.iri, property.data_type, happening, event)
					property.add_occurrence(property_occurrence)

	def add_required_property_occurence(self, iri: str, data_type: str, relation_type: str, capability_iris: Set[str]) -> None:
		property = Property(iri, data_type, relation_type, capability_iris)
		self.required_properties.setdefault(iri, property)
		property_occurence = PropertyOccurrence(iri, data_type, 0, 0)
		self.required_properties[iri].add_occurrence(property_occurence)

	def get_required_property_occurrence(self, iri: str) -> PropertyOccurrence:
		if (not iri in self.required_properties):
			raise KeyError(f"There is no required property with key {iri}.")
		# Required props only have one entry, so return 0,0
		return self.required_properties[iri].occurrences[0][0]

	def get_provided_property_occurrence(self, iri: str, happening:int, event:int) -> PropertyOccurrence:
		if (not iri in self.provided_properties):
			raise KeyError(f"There is no provided property with key {iri} at happening {happening} and event {event}.")
		return self.provided_properties[iri].occurrences[happening][event]

	def get_property_occurence(self, iri: str, happening:int, event:int) -> PropertyOccurrence:
		try:
			property = self.get_required_property_occurrence(iri)
		except KeyError:
			try:
				property = self.get_provided_property_occurrence(iri, happening, event)
			except KeyError:
				raise KeyError(f"There is neither a provided nor a required property with key {str(iri)}.")
		return property

	def get_provided_property(self, iri:str) -> Property:
		if (not iri in self.provided_properties):
			raise KeyError(f"There is no provided property with key {iri}.")
		return self.provided_properties[iri]

	def get_property(self, iri:str) -> Property:
		all_properties = {**self.required_properties, **self.provided_properties}
		if (not iri in all_properties):
			raise KeyError(f"There is no property with key {iri}.")
		return all_properties[iri]

	def get_property_data_type(self, iri: str):
		property = self.get_property(iri)
		return property.data_type
	
	def get_property_relation_type(self, iri: str) -> str:
		property = self.get_property(iri)
		return property.relation_type
	
	def get_property_from_z3_variable(self, z3_variable: AstRef) -> PropertyOccurrence:
		all_properties = {**self.required_properties, **self.provided_properties}
		for property in all_properties.values():
			property_occurrence = property.get_occurrence_by_z3_variable(str(z3_variable))
			if property_occurrence is not None:
				return property_occurrence
		
		raise KeyError(f"There is not a single property occurrence for the z3_variable {z3_variable}")
	
	@staticmethod
	def create_instance_description(iri: str, cap_iri: str, cap_type: CapabilityType, expr_goal: str, logical_interpretation: str, value: str):
		if expr_goal == "Requirement":
			if cap_type == CapabilityType.RequiredCapability:
				return Goal(iri, cap_iri, logical_interpretation, value)
			return Precondition(iri, cap_iri, logical_interpretation, value)
		elif expr_goal == "Assurance":
			return Effect(iri, cap_iri, logical_interpretation, value)
		elif expr_goal == "Actual_Value":
			return Init(iri, cap_iri, logical_interpretation, value)
		else:
			raise ValueError(f"InstanceDescription with Expression Goal {expr_goal} is not supported.")

	def add_instance_description(self, iri: str, cap_iri: str, cap_type: CapabilityType, expr_goal: str, logical_interpretation: str, value: str):
		instance_description = self.create_instance_description(iri, cap_iri, cap_type, expr_goal, logical_interpretation, value)
		if isinstance(instance_description, Precondition):
			self.preconditions.setdefault(iri, instance_description)
		elif isinstance(instance_description, Effect):
			self.effects.setdefault(iri, instance_description)
		elif isinstance(instance_description, Init):
			self.inits.setdefault(iri, instance_description)
		elif isinstance(instance_description, Goal):
			self.goals.setdefault(iri, instance_description)

    # TODO after combining query of precondition and property move this function to add provided property 
	# def add_precondition_property(self, iri: str, cap_iri: str, logical_interpretation: str, value: str):    
	# 	precondition = Precondition(iri, cap_iri, logical_interpretation, value)
	# 	self.preconditions.setdefault(iri, precondition)

	def get_preconditions(self) -> Dict[str, Precondition]:
		return self.preconditions
	
	def get_effects(self) -> Dict[str, Effect]:
		return self.effects
	
	def get_inits(self) -> Dict[str, Init]:
		return self.inits
	
	def get_goals(self) -> Dict[str, Goal]:
		return self.goals