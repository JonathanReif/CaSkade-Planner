from rdflib import Graph
from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary


def getAllProperties(graph: Graph, happenings:int, eventBound:int) -> PropertyDictionary :
	'''Create names for all properties related to the provided capabilities'''
	
	# Names need to be a combination of the thing that has a property (ID) with the corresponding type description. 
	# Thing and type description together define a certain property in a context.
	queryString = """
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT DISTINCT ?de ?dataType WHERE { 
		?cap a CaSk:ProvidedCapability;
		^CSS:requiresCapability ?process.
		?process VDI3682:hasInput|VDI3682:hasOutput ?inout.
		?inout VDI3682:isCharacterizedBy ?id.
		?de DINEN61360:has_Instance_Description ?id.
		?id a ?dataType.
		?dataType rdfs:subClassOf DINEN61360:Simple_Data_Type.
	}"""
	
	results = graph.query(queryString)
	properties = PropertyDictionary()
	for row in results:
		for happening in range(happenings):
			for event in range(eventBound):
				properties.addEntry(str(row.de), str(row.dataType), event, happening)
	return properties




def getProvidedCapabilities(graph:Graph, happenings:int, eventBound:int) -> CapabilityDictionary :
	'''Get all provided capabilities'''

	queryString = """
	PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>
	SELECT ?cap WHERE { 
		?cap a cask:ProvidedCapability. 
	} """

	results = graph.query(queryString)
	capDict = CapabilityDictionary()
	for row in results: 
		for happening in range(happenings): 
			capDict.addEntry(str(row.cap), happening)

	return capDict