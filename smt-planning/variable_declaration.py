from rdflib import Graph
from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary


def getAllProperties(graph: Graph, happenings:int, eventBound:int) -> PropertyDictionary :
	'''Create names for all properties related to the provided capabilities'''
	
	# Names need to be a combination of the thing that has a property (ID) with the corresponding type description. 
	# Thing and type description together define a certain property in a context.
	# rdflib is not capable of inferencing 
	queryString = """
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT DISTINCT ?de ?dataType ?relationType WHERE { 
		?cap a ?capType;
			^CSS:requiresCapability ?process.
		values ?capType { CaSk:ProvidedCapability CaSk:RequiredCapability }. 	
		?process ?relation ?inout.
		VALUES ?relation {VDI3682:hasInput VDI3682:hasOutput}.
		?inout VDI3682:isCharacterizedBy ?id.
		?de DINEN61360:has_Instance_Description ?id.
		?id a ?dataType.
		?dataType rdfs:subClassOf DINEN61360:Simple_Data_Type.
		BIND(STRAFTER(STR(?relation), "has") AS ?relationType)
	}"""
	
	results = graph.query(queryString)
	properties = PropertyDictionary()
	for row in results:
		properties.addProperty(row.de, str(row.dataType), str(row.relationType)) # type: ignore 
		for happening in range(happenings):
			properties.addPropertyHappening(row.de, happening) # type: ignore
			for event in range(eventBound):
				properties.addPropertyEvent(row.de, str(row.dataType), happening, event) # type: ignore
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
		capDict.addCapability(row.cap)					#type: ignore
		for happening in range(happenings): 
			capDict.addCapabilityHappening(row.cap, happening) # type: ignore

	return capDict