from typing import Dict, List, Tuple
from z3 import *
from rdflib import URIRef

class ProvidedPropertyEntry:
	def __init__(self, type: str, relation_type: str, states: Dict[int, Dict]):
		self.type = type
		self.relation_type = relation_type
		self.states = states

class RequiredPropertyEntry:
	def __init__(self, type: str, relation_type: str, variable: ArithRef | BoolRef):
		self.type = type
		self.relation_type = relation_type
		self.variable = variable

class ReversedPropertyEntry:
	def __init__(self, iri: URIRef, type: str, relation_type: str, variable: ArithRef | BoolRef):
		self.iri = iri
		self.type = type
		self.relation_type = relation_type
		self.variable = variable

class PropertyDictionary:
	def __init__(self):
		self.provided_properties: Dict[str, ProvidedPropertyEntry] = dict()
		self.required_properties: Dict[str, RequiredPropertyEntry] = dict()
		self.reversed_provided_property_index: Dict[Tuple, List[ReversedPropertyEntry]] = dict()

	def add_provided_property(self, iri:URIRef, type:str, relation_type:str):
		self.provided_properties[str(iri)] = ProvidedPropertyEntry(type, relation_type, dict())

	def add_required_property(self, iri:URIRef, type:str, relation_type:str):
		variable_name = str(iri)
		match type:
			case "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":
				new_var = Real(variable_name)
			case "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
				new_var = Bool(variable_name)
			case "http://www.hsu-ifa.de/ontologies/DINEN61360#Integer":
				new_var = Int(variable_name)
			case _  :
				# Base case if no type given: Create a real
				new_var = Real(variable_name)
		self.required_properties[str(iri)] = RequiredPropertyEntry(type, relation_type, new_var)

	def addPropertyHappening(self, iri:URIRef, happening:int):
		self.provided_properties[str(iri)].states[happening] = {}

	def addPropertyEvent(self, iri:URIRef, type:str, happening: int, event: int):
		# self.properties[iri] = PropertyEntry(type, dict())
		iriString = str(iri)
		variableName = iriString + "_" + str(happening) + "_" + str(event)
		# self.properties[iriString].states[event] = {}
		match type:
			case "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":
				new_var = Real(variableName)
			case "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
				new_var = Bool(variableName)
			case "http://www.hsu-ifa.de/ontologies/DINEN61360#Integer":
				new_var = Int(variableName)
			case _  :
				# Base case if no type given: Create a real
				new_var = Real(variableName)

		self.provided_properties[iriString].states[happening][event] = new_var
		relation_type = self.provided_properties[iriString].relation_type
		self.reversed_provided_property_index.setdefault((happening,event), []).append(ReversedPropertyEntry(iri, type, relation_type, new_var))

	def get_required_property(self, iri: URIRef) -> ArithRef | BoolRef:
		iriString = str(iri)
		if (not iriString in self.required_properties):
			raise KeyError(f"There is no required property with key {iriString}.")
		return self.required_properties[iriString].variable

	def get_provided_property(self, iri: URIRef, happening:int, event:int) -> ArithRef | BoolRef:
		iriString = str(iri)
		if (not iriString in self.provided_properties):
			raise KeyError(f"There is no provided property with key {iriString}.")
		return self.provided_properties[iriString].states[happening][event]
	
	def get_provided_properties_at_happening_and_event(self, happening: int, event:int) -> List[ReversedPropertyEntry]:
		return self.reversed_provided_property_index[(happening, event)]
	

	def get_property(self, iri: URIRef, happening:int, event:int):
		try:
			property = self.get_required_property(iri)
		except KeyError:
			try:
				property = self.get_provided_property(iri, happening, event)
			except KeyError:
				raise KeyError(f"There is neither a provided nor a required property with key {str(iri)}.")
		return property

	def get_property_type(self, iri: URIRef):
		all_properties = {**self.required_properties, **self.provided_properties}
		return all_properties[str(iri)].type
	
	def get_relation_type_of_property(self, iri: URIRef) -> str:
		all_properties = {**self.required_properties, **self.provided_properties}
		return all_properties[str(iri)].relation_type