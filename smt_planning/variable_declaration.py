from rdflib import Graph
from typing import List
from smt_planning.StateHandler import StateHandler
from smt_planning.dicts.CapabilityDictionary import CapabilityDictionary, CapabilityPropertyInfluence, PropertyChange
from smt_planning.dicts.PropertyDictionary import PropertyDictionary


def getAllProperties(happenings:int, eventBound:int) -> PropertyDictionary :
	
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
	graph = StateHandler().get_graph()
	results = graph.query(queryString)
	properties = PropertyDictionary()
	for row in results:
		caps = set(row.caps.split(","))
		
		if str(row.capType) == "http://www.w3id.org/hsu-aut/cask#RequiredCapability":
			properties.add_required_property_occurence(str(row.de), str(row.dataType), str(row.relationType), caps)  
			continue

		
		# properties.add_provided_property(str(row.de), str(row.dataType), str(row.relationType), happening, event, caps)  
		for happening in range(happenings):
			# properties.addPropertyHappening(row.de, happening) 
			for event in range(eventBound):
				properties.add_provided_property_occurence(str(row.de), str(row.dataType), str(row.relationType), happening, event, caps)  
				# property_occurence = PropertyOccurrence(str(row.de), str(row.dataType), str(row.relationType), happening, event, caps)
				# properties.addPropertyEvent(property_occurence) 
	return properties


def get_provided_capabilities(happenings:int) -> CapabilityDictionary :
	queryString = """
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	SELECT ?cap ?de WHERE { 
		?cap a CaSk:ProvidedCapability;
			^CSS:requiresCapability ?process.
		?process VDI3682:hasInput ?input.
		?input VDI3682:isCharacterizedBy ?id.
		?de DINEN61360:has_Instance_Description ?id.
	}
	"""
	graph = StateHandler().get_graph()
	results = graph.query(queryString)
	property_dictionary = StateHandler().get_property_dictionary()
	capability_dictionary = CapabilityDictionary()

	caps = set([str(row.cap) for row in results])
	for cap in caps:
		# Input properties can be retrieved from query
		inputs = [str(row.de) for row in results if (str(row.cap) == cap)]
		input_properties = [property_dictionary.get_property(input) for input in inputs]
		# Outputs need to have their effect attached and are more tricky
		outputs = get_output_influences_of_capability(graph, cap)
		for happening in range(happenings): 
			capability_dictionary.add_capability_occurrence(cap, "http://www.w3id.org/hsu-aut/cask#ProvidedCapability", happening, input_properties, outputs)

	return capability_dictionary


# TODO: Can both functions be done with one query?
def get_output_influences_of_capability(graph:Graph, capability_iri: str) -> List[CapabilityPropertyInfluence] :
	'''Get all provided capabilities'''

	queryString = """
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX OM: <http://openmath.org/vocab/math#>
	PREFIX OM-Relation1: <http://www.openmath.org/cd/relation1#>
	SELECT * WHERE {
		BIND(<{capability_iri}> AS ?cap)
		?cap a CaSk:ProvidedCapability;
			^CSS:requiresCapability ?process.	
		?process VDI3682:hasInput ?input.
		?input VDI3682:isCharacterizedBy ?input_id.
		?input_de DINEN61360:has_Instance_Description ?input_id;
			DINEN61360:has_Type_Description ?td.
		?input_id a ?dataType.
		?dataType rdfs:subClassOf DINEN61360:Simple_Data_Type.
		OPTIONAL {
			?input_id DINEN61360:Expression_Goal ?inputExpressionGoal.
		}
		OPTIONAL {
			?input_id DINEN61360:Value ?inputValue.
		}
		
		?process VDI3682:hasOutput ?output.
		?output VDI3682:isCharacterizedBy ?output_id.
		?output_de DINEN61360:has_Instance_Description ?output_id;
			DINEN61360:has_Type_Description ?td.
		?output_id a ?dataType.
		OPTIONAL {
			?output_id DINEN61360:Value ?outputValue.
		}
		OPTIONAL {
			?capability CSS:isRestrictedBy ?equalConstraint.
			?equalConstraint OM:arguments/rdf:rest/rdf:first|OM:arguments/rdf:first ?input_id;
				OM:arguments/rdf:rest/rdf:first|OM:arguments/rdf:first ?output_id;
									OM:operator OM-Relation1:eq.
		}
	} """
	queryString = queryString.replace("{capability_iri}", capability_iri)
	results = graph.query(queryString)
	property_dictionary = StateHandler().get_property_dictionary()
	influences: List[CapabilityPropertyInfluence] = []
	for row in results: 
		# for happening in range(happenings): 
		# capDict.add_CapabilityOccurrence(str(row.cap), "http://www.w3id.org/hsu-aut/cask#ProvidedCapability", happening, [], [])
		property_iri = str(row.output_de)
		prop = property_dictionary.get_property(property_iri)
		if(not row.equalConstraint and not row.outputValue and not row.inputValue):
			continue
		if(row.equalConstraint):
			if(row.inputExpressionGoal):
				# Case of requirements or actual values. In this case, prop has a constant value and output is set to equal
				effect = PropertyChange.NoChange
			else:
				# Case of no expression goal, i.e., free parameter. In this case, prop is changed to the free parameter
				effect = PropertyChange.ChangeByExpression
		else:
			if (row.outputValue and row.outputValue.eq(row.inputValue)):
				# Simple case: both input and output have the same static value
				effect = PropertyChange.NoChange
			elif (row.outputValue and not row.outputValue.eq(row.inputValue)):
				if str(row.outputValue).lower() == "false":
					effect = PropertyChange.SetFalse
				elif str(row.outputValue).lower() == "true":
					effect = PropertyChange.SetTrue
				else:
					# Numeric change
					effect = PropertyChange.NumericConstant

		influence = CapabilityPropertyInfluence(prop, effect)
		influences.append(influence)

	return influences