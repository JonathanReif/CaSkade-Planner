from rdflib import Graph
from typing import List
		
class PropertyResult: 
	realProperties= []
	boolProperties = []
	integerProperties = []

def getAllProperties(graph: Graph, happenings:int, eventBound:int) -> PropertyResult :
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
	properties = PropertyResult()
	for row in results:
		for happening in range(happenings):
			for event in range(eventBound):
				propName = str(row.prop) + "_" + str(event) + "_" + str(happening)
				if(row.dataType == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real"):
					properties.realProperties.append(propName)
				if(row.dataType == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean"):
					properties.boolProperties.append(propName)
				if(row.dataType == "http://www.hsu-ifa.de/ontologies/DINEN61360#Integer"):
					properties.integerProperties.append(propName)
	return properties


def getProvidedCapabilities(graph:Graph, happenings:int, eventBound:int) -> List :
	'''Get all provided capabilities'''

	queryString = """
	PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>
	SELECT ?cap WHERE { 
		?cap a cask:ProvidedCapability. 
	} """

	results = graph.query(queryString)
	capabilities = []
	for row in results: 
		for happening in range(happenings): 
			capName = str(row.cap) + "_" + str(happening)
			capabilities.append(capName)

	return capabilities

	# '''
	# Get all properties of capability (e.g. longitude) besides information outputs with assurance and information inputs requirements
	# Transform capability properties to smt variables for every event(2) and every happening
	# TODO: check if property is a boolean or a real (über TypeDescription --> Unit of Measure??)
	# '''
	# results = g.query(sparql_queries.get_sparql_cap_props())
	# cap_props = []

	# for row in results: 
	# 	for happening in range(happenings): 
	# 		for event in range(2):
	# 			cap_prop_name = str(row.prop) + "_" + str(event) + "_" + str(happening)
	# 			cap_prop = Real(cap_prop_name)
	# 			cap_props.append(cap_prop)