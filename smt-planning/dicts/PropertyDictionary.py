from typing import Dict, Set, List, Tuple
from z3 import *

class PropertyOccurrence:
	def __init__(self, iri: str, data_type: str, happening: int, event: int,):
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

# TODO: Comment what this exactly is in the ontology(DE, ID, ..)?
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
		self.provided_properties: Dict[str, Property] = {}
		# self.provided_properties: List[PropertyOccurrence] = []
		self.required_properties: Dict[str, Property] = {}
		# self.reversed_provided_property_index: Dict[Tuple, List[ReversedPropertyEntry]] = dict()

	def add_provided_property_occurence(self, iri: str, data_type: str, relation_type: str, happening: int, event: int, capability_iris: Set[str]):
		property = Property(iri, data_type, relation_type, capability_iris)
		self.provided_properties.setdefault(iri, property)
		property_occurence = PropertyOccurrence(iri, data_type, happening, event)
		self.provided_properties[iri].add_occurrence(property_occurence)

	def add_required_property_occurence(self, iri: str, data_type: str, relation_type: str, capability_iris: Set[str]):
		property = Property(iri, data_type, relation_type, capability_iris)
		self.required_properties.setdefault(iri, property)
		property_occurence = PropertyOccurrence(iri, data_type, 0, 0)
		self.required_properties[iri].add_occurrence(property_occurence)

	# def addPropertyHappening(self, iri:URIRef, happening:int):
	# 	self.provided_properties[str(iri)].states[happening] = {}

	# def addPropertyEvent(self, property_occurrence: PropertyOccurrence):
	# 	self.provided_properties[iriString].states[happening][event] = property_occurrence
		
	# 	self.reversed_provided_property_index.setdefault((happening,event), []).append(ReversedPropertyEntry(iri, type, relation_type, new_var))

	def get_required_property_occurrence(self, iri: str) -> PropertyOccurrence:
		if (not iri in self.required_properties):
			raise KeyError(f"There is no required property with key {iri}.")
		# Required props only have one entry, so return 0,0
		return self.required_properties[iri].occurrences[0][0]

	def get_provided_property_occurrence(self, iri: str, happening:int, event:int) -> PropertyOccurrence:
		if (not iri in self.provided_properties):
			raise KeyError(f"There is no provided property with key {iri} at happening {happening} and event {event}.")
		return self.provided_properties[iri].occurrences[happening][event]
	
	# def get_provided_properties_at_happening_and_event(self, happening: int, event:int) -> List[PropertyOccurrence]:
	# 	selected_provided_properties = [property for property in self.provided_properties if ((property.happening == happening) and (property.event == event))]
	# 	if (len(selected_provided_properties) == 0):
	# 		raise KeyError(f"There is no provided property with at happening {happening} and event {event}.")
	# 	return selected_provided_properties
	

	def get_property_occurence(self, iri: str, happening:int, event:int) -> PropertyOccurrence:
		try:
			property = self.get_required_property_occurrence(iri)
		except KeyError:
			try:
				property = self.get_provided_property_occurrence(iri, happening, event)
			except KeyError:
				raise KeyError(f"There is neither a provided nor a required property with key {str(iri)}.")
		return property

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