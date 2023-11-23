from typing import List
from rdflib import Graph

from smt_planning.dicts.CapabilityDictionary import CapabilityDictionary
from smt_planning.dicts.PropertyDictionary import PropertyDictionary

# Singleton class
class StateHandler:
	
	_instance = None

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super(StateHandler, cls).__new__(cls)
			cls.__graph = None
			cls.__property_dictionary = None
			cls.__capability_dictionary = None
			from smt_planning.smt.capability_links import CapabilityPairCache
			from smt_planning.smt.property_links import PropertyPairCache
			cls.__property_pair_cache = CapabilityPairCache
			cls.__capability_pair_cache = PropertyPairCache
			# Put any initialization here.
		return cls._instance

	def set_graph(self, graph: Graph):
		self.__graph = graph
	
	def get_graph(self) -> Graph:
		return self.__graph

	def set_property_dictionary(self, property_dictionary: PropertyDictionary):
		self.__property_dictionary = property_dictionary
	
	def get_property_dictionary(self) -> PropertyDictionary:
		return self.__property_dictionary
	
	def set_capability_dictionary(self, capability_dictionary: CapabilityDictionary):
		self.__capability_dictionary = capability_dictionary
	
	def get_capability_dictionary(self) -> CapabilityDictionary:
		return self.__capability_dictionary
	
	def reset_caches(self):
		self.__property_pair_cache.reset()
		self.__capability_pair_cache.reset()
