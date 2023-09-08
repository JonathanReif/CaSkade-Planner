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

	def addPropertyStates(self, iri:URIRef, type:str, event:int, happening: int):
		# self.properties[iri] = PropertyEntry(type, dict())
		iriString = str(iri)
		variableName = iriString + "_" + str(event) + "_" + str(happening)
		self.properties[iriString].states[event] = {}
		if type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":
			self.properties[iriString].states[event][happening] = Real(variableName)
		if type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
			self.properties[iriString].states[event][happening] = Bool(variableName)
		if type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Integer":
			self.properties[iriString].states[event][happening] = Int(variableName)

	def getPropertyVariable(self, iri: URIRef, event:int, happening:int):
		iriString = str(iri)
		if (not iriString in self.properties):
			raise KeyError(f"These is no property with key {iriString}.")
		return self.properties[iriString].states[event][happening]
	
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