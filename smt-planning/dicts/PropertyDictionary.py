from typing import Dict, List, Tuple
from z3 import *
from rdflib import URIRef

class PropertyEntry:
	def __init__(self, type: str, relation_type: str, states: Dict[int, Dict]):
		self.type = type
		self.relation_type = relation_type
		self.states = states

class ReversedPropertyEntry:
	def __init__(self, iri: URIRef, type: str, relation_type: str, variable: ArithRef | BoolRef):
		self.iri = iri
		self.type = type
		self.relation_type = relation_type
		self.variable = variable

class PropertyDictionary:
	def __init__(self):
		self.properties: Dict[str, PropertyEntry] = dict()
		self.property_index: Dict[Tuple, List[ReversedPropertyEntry]] = dict()

	def addProperty(self, iri:URIRef, type:str, relation_type:str):
		self.properties[str(iri)] = PropertyEntry(type, relation_type, dict())

	def addPropertyHappening(self, iri:URIRef, happening:int):
		self.properties[str(iri)].states[happening] = {}

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

		self.properties[iriString].states[happening][event] = new_var
		relation_type = self.properties[iriString].relation_type
		self.property_index.setdefault((happening,event), []).append(ReversedPropertyEntry(iri, type, relation_type, new_var))

	def getPropertyVariable(self, iri: URIRef, happening:int, event:int):
		iriString = str(iri)
		if (not iriString in self.properties):
			raise KeyError(f"There is no property with key {iriString}.")
		return self.properties[iriString].states[happening][event]
	
	def get_properties_at_happening_and_event(self, happening: int, event:int) -> List[ReversedPropertyEntry]:
		return self.property_index[(happening, event)]
	
	def getPropertyType(self, iri: URIRef):
		return self.properties[str(iri)].type
	
	def get_relation_type_of_property(self, iri: URIRef) -> str:
		return self.properties[str(iri)].relation_type
	
	# def getAllRealVariableStates(self) -> List:
	# 	filteredEntries =  list(filter(self.isRealVariable, self.properties.values()))
	# 	flatList = []
	# 	for entry in filteredEntries:
	# 		flattedEntryList = [item for sublist in entry.states for item in sublist]
	# 		flatList.extend(flattedEntryList)
	# 	return flatList
	
	# def getAllBoolVariableStates(self) -> List:
	# 	filteredEntries =  list(filter(self.isBoolVariable, self.properties.values()))
	# 	flatList = []
	# 	for entry in filteredEntries:
	# 		flattedEntryList = [item for sublist in entry.states for item in sublist]
	# 		flatList.extend(flattedEntryList)
	# 	return flatList
	
	# def getAllIntVariableStates(self) -> List:
	# 	filteredEntries =  list(filter(self.isIntVariable, self.properties.values()))
	# 	flatList = []
	# 	for entry in filteredEntries:
	# 		flattedEntryList = [item for sublist in entry.states for item in sublist]
	# 		flatList.extend(flattedEntryList)
	# 	return flatList

	# def isRealVariable(self, entry: PropertyEntry) -> bool:
	# 	return entry.type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real"
	
	# def isBoolVariable(self, entry: PropertyEntry) -> bool:
	# 	return entry.type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean"
	
	# def isIntVariable(self, entry: PropertyEntry) -> bool:
	# 	return entry.type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Integer"