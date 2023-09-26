from typing import Dict, Set, List, Tuple
from z3 import *

class PropertyOccurrence:
	def __init__(self, iri: str, data_type: str, relation_type: str, happening: int, event: int, capability_iris: Set[str]):
		self.iri = iri
		self.happening = happening
		self.event = event
		self.data_type = data_type
		self.relation_type = relation_type
		self.capability_iris = capability_iris
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

# class ProvidedPropertyEntry:
# 	def __init__(self, type: str, relation_type: str, states: Dict[Tuple[int, int], PropertyOccurrence]):
# 		self.type = type
# 		self.relation_type = relation_type
# 		self.states = states

# class RequiredPropertyEntry:
# 	def __init__(self, type: str, relation_type: str, variable: ArithRef | BoolRef):
# 		self.type = type
# 		self.relation_type = relation_type
# 		self.variable = variable

# class ReversedPropertyEntry:
# 	def __init__(self, iri: URIRef, type: str, relation_type: str, variable: ArithRef | BoolRef):
# 		self.iri = iri
# 		self.type = type
# 		self.relation_type = relation_type
# 		self.variable = variable

class PropertyDictionary:
	def __init__(self):
		self.provided_properties: List[PropertyOccurrence] = []
		self.required_properties: List[PropertyOccurrence] = []
		# self.reversed_provided_property_index: Dict[Tuple, List[ReversedPropertyEntry]] = dict()

	def add_provided_property(self, iri: str, data_type: str, relation_type: str, happening: int, event: int, capability_iris: Set[str]):
		property_occurence = PropertyOccurrence(iri, data_type, relation_type, happening, event, capability_iris)
		self.provided_properties.append(property_occurence)

	def add_required_property(self, iri: str, data_type: str, relation_type: str, capability_iris: Set[str]):
		property_occurence = PropertyOccurrence(iri, data_type, relation_type, 0, 0, capability_iris)
		self.required_properties.append(property_occurence)

	# def addPropertyHappening(self, iri:URIRef, happening:int):
	# 	self.provided_properties[str(iri)].states[happening] = {}

	# def addPropertyEvent(self, property_occurrence: PropertyOccurrence):
	# 	self.provided_properties[iriString].states[happening][event] = property_occurrence
		
	# 	self.reversed_provided_property_index.setdefault((happening,event), []).append(ReversedPropertyEntry(iri, type, relation_type, new_var))

	def get_required_property(self, iri: str) -> PropertyOccurrence:
		selected_required_properties = [property for property in self.required_properties if property.iri == iri]
		if (len(selected_required_properties) == 0):
			raise KeyError(f"There is no required property with key {iri}.")
		if (len(selected_required_properties) > 1):
			raise KeyError(f"Multiple required properties with {iri} found.")
		return selected_required_properties[0]

	def get_provided_property(self, iri: str, happening:int, event:int) -> PropertyOccurrence:
		selected_provided_properties = [property for property in self.provided_properties if ((property.iri == iri) and (property.happening == happening) and (property.event == event))]
		if (len(selected_provided_properties) == 0):
			raise KeyError(f"There is no provided property with key {iri} at happening {happening} and event {event}.")
		if (len(selected_provided_properties) > 1):
			raise KeyError(f"Multiple provided properties with IRI '{iri}', happening {happening} and event {event} found.")
		return selected_provided_properties[0]
	
	def get_provided_properties_at_happening_and_event(self, happening: int, event:int) -> List[PropertyOccurrence]:
		selected_provided_properties = [property for property in self.provided_properties if ((property.happening == happening) and (property.event == event))]
		if (len(selected_provided_properties) == 0):
			raise KeyError(f"There is no provided property with at happening {happening} and event {event}.")
		return selected_provided_properties
	

	def get_property(self, iri: str, happening:int, event:int) -> PropertyOccurrence:
		try:
			property = self.get_required_property(iri)
		except KeyError:
			try:
				property = self.get_provided_property(iri, happening, event)
			except KeyError:
				raise KeyError(f"There is neither a provided nor a required property with key {str(iri)}.")
		return property

	def get_property_data_type(self, iri: str):
		all_properties = [*self.required_properties, *self.provided_properties]
		properties = [property for property in all_properties if property.iri == iri]
		if (len(properties) == 0):
			raise KeyError(f"There is no property with key {iri}.")
		return properties[0].data_type
	
	def get_property_relation_type(self, iri: str) -> str:
		all_properties = [*self.required_properties, *self.provided_properties]
		properties = [property for property in all_properties if property.iri == iri]
		if (len(properties) == 0):
			raise KeyError(f"There is no property with key {iri}.")
		return properties[0].relation_type