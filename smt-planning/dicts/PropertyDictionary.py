from typing import Dict, Union
from z3 import *
from rdflib import URIRef

class PropertyEntry:
	def __init__(self, type: str, states: Dict[int, Dict]):
		self.type = type
		self.states = states

class PropertyDictionary:
	def __init__(self):
		self.properties: Dict[str, PropertyEntry] = dict()

	def addProperty(self, iri:URIRef, type:str):
		self.properties[str(iri)] = PropertyEntry(type, dict())

	def addPropertyHappening(self, iri:URIRef, happening:int):
		self.properties[str(iri)].states[happening] = {}

	def addPropertyEvent(self, iri:URIRef, type:str, happening: int, event: int):
		# self.properties[iri] = PropertyEntry(type, dict())
		iriString = str(iri)
		variableName = iriString + "_" + str(happening) + "_" + str(event)
		# self.properties[iriString].states[event] = {}
		if type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":
			self.properties[iriString].states[happening][event] = Real(variableName)
		if type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
			self.properties[iriString].states[happening][event] = Bool(variableName)
		if type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Integer":
			self.properties[iriString].states[happening][event] = Int(variableName)

	def getPropertyVariable(self, iri: URIRef, happening:int, event:int):
		iriString = str(iri)
		if (not iriString in self.properties):
			raise KeyError(f"There is no property with key {iriString}.")
		return self.properties[iriString].states[happening][event]
	
	def getPropertyType(self, iri: URIRef):
		return self.properties[str(iri)].type
	
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