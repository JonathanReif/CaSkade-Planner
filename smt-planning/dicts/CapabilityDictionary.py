from typing import Dict
from z3 import Bool, BoolRef
from rdflib import URIRef

class CapabilityDictionary:
	def __init__(self):
		self.capabilities: Dict[str, Dict[int, BoolRef]] = dict()

	def addCapability(self, iri:URIRef):
		self.capabilities[str(iri)] = {}

	def addCapabilityHappening(self, iri:URIRef, happening: int):
		variableName = str(iri) + "_" + str(happening)
		self.capabilities[str(iri)][happening] = Bool(variableName)

	def getCapabilityVariableByIriAndHappening(self, iri: URIRef, happening:int) -> BoolRef:
		return self.capabilities[str(iri)][happening]