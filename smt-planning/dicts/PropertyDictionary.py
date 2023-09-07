from typing import Dict, Union
from z3 import *

class PropertyEntry:
	def __init__(self, type: str, states: Dict[int, Dict]):
		self.type = type
		self.states = states


class PropertyDictionary:
	def __init__(self):
		self.properties: Dict[str, PropertyEntry] = dict()

	def addEntry(self, iri:str, type:str, event:int, happening: int):
		self.properties[iri] = PropertyEntry(type, dict())
		variableName = str(iri) + "_" + str(event) + "_" + str(happening)
		self.properties[iri].states[event] = {}
		if type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":
			self.properties[iri].states[event][happening] = Real(variableName)
		if type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
			self.properties[iri].states[event][happening] = Bool(variableName)
		if type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Integer":
			self.properties[iri].states[event][happening] = Int(variableName)

	def getPropertyVariable(self, iri: str, event:int, happening:int):
		return self.properties[iri].states[event][happening]
	
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