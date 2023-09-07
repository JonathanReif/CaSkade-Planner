from typing import Dict
from z3 import Bool, BoolRef

class CapabilityDictionary:
	def __init__(self):
		self.capabilities: Dict[str, Dict[int, BoolRef]] = dict()

	def addEntry(self, iri:str, happening: int):
		variableName = str(iri) + "_" + str(happening)
		self.capabilities[iri] = {}
		self.capabilities[iri][happening] = Bool(variableName)

	def getCapabilityVariableByIriAndHappening(self, iri: str, happening:int) -> BoolRef:
		return self.capabilities[iri][happening]