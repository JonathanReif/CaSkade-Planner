from rdflib import Graph
from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary, PropertyOccurrence


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
	SELECT ?de (GROUP_CONCAT(?cap; SEPARATOR=",") AS ?caps) ?capType ?dataType ?relationType WHERE { 
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
	} GROUP BY ?de ?capType ?dataType ?relationType
	"""
	
	results = graph.query(queryString)
	properties = PropertyDictionary()
	for row in results:
		caps = set(row.caps.split(","))
		
		if str(row.capType) == "http://www.w3id.org/hsu-aut/cask#RequiredCapability":
			properties.add_required_property(str(row.de), str(row.dataType), str(row.relationType), caps)  
			continue

		
		# properties.add_provided_property(str(row.de), str(row.dataType), str(row.relationType), happening, event, caps)  
		for happening in range(happenings):
			# properties.addPropertyHappening(row.de, happening) 
			for event in range(eventBound):
				properties.add_provided_property(str(row.de), str(row.dataType), str(row.relationType), happening, event, caps)  
				# property_occurence = PropertyOccurrence(str(row.de), str(row.dataType), str(row.relationType), happening, event, caps)
				# properties.addPropertyEvent(property_occurence) 
	return properties



# TODO: Can both functions be done with one query?
def getProvidedCapabilities(graph:Graph, happenings:int) -> CapabilityDictionary :
	'''Get all provided capabilities'''

	queryString = """
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	SELECT ?cap WHERE { 
		?cap a CaSk:ProvidedCapability;
			^CSS:requiresCapability ?process.
		?process ?relation ?inout.
		VALUES ?relation {VDI3682:hasInput VDI3682:hasOutput}.
		?inout VDI3682:isCharacterizedBy ?id.
		?de DINEN61360:has_Instance_Description ?id.
		?id a ?dataType.
		?dataType rdfs:subClassOf DINEN61360:Simple_Data_Type.
		BIND(STRAFTER(STR(?relation), "has") AS ?relationType)
	} """
	results = graph.query(queryString)
	
	caps = set([str(row.cap) for row in results])
	capDict = CapabilityDictionary()
	for cap in caps:
		for happening in range(happenings): 
			capDict.add_CapabilityOccurrence(cap, "http://www.w3id.org/hsu-aut/cask#ProvidedCapability", happening, [], [])
	# for row in results: 
	# 	for happening in range(happenings): 
	# 		capDict.add_CapabilityOccurrence(str(row.cap), "http://www.w3id.org/hsu-aut/cask#ProvidedCapability", happening, [], [])

	return capDict