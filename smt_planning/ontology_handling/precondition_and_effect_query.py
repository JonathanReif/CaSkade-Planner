from smt_planning.smt.StateHandler import StateHandler

def get_capability_preconditions():

	# Get all resource properties for capability precondition that has to be compared with input information property (Requirement). 
	# TODO combine query with property query 
	query_string = """
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>

	SELECT ?cap ?de ?log ?val WHERE {  
		?cap a CaSk:ProvidedCapability;
			^CSS:requiresCapability ?process.
		?process VDI3682:hasInput ?input.
		?input VDI3682:isCharacterizedBy ?id.
		?id DINEN61360:Expression_Goal "Requirement";
			DINEN61360:Logic_Interpretation ?log;
			DINEN61360:Value ?val.
		?de DINEN61360:has_Instance_Description ?id.
	} 
	"""
	stateHandler = StateHandler()
	query_handler = stateHandler.get_query_handler()
	property_dictionary = stateHandler.get_property_dictionary()
	results = query_handler.query(query_string)
	for row in results:
		property_dictionary.add_instance_description(str(row['de']), str(row['cap']), "Requirement", str(row['log']), str(row['val'])) #type: ignore
		
def get_capability_effects():
	
	# Effect 1. Fall Assurance mit statischem Value

	# Get all capability outputs  
	query_string = """
	PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>

	select ?cap ?de ?log ?val where {  
		?cap a cask:ProvidedCapability;
			^CSS:requiresCapability ?process.
		?process VDI3682:hasOutput ?output.
		?output VDI3682:isCharacterizedBy ?id.
		?id DINEN61360:Expression_Goal "Assurance";
			DINEN61360:Logic_Interpretation ?log.
		?de DINEN61360:has_Instance_Description ?id.
		OPTIONAL { ?id DINEN61360:Value ?val. }
	} """
	stateHandler = StateHandler()
	query_handler = stateHandler.get_query_handler()
	property_dictionary = stateHandler.get_property_dictionary()
	results = query_handler.query(query_string)
	for row in results:
		property_dictionary.add_instance_description(str(row['de']), str(row['cap']), "Assurance", str(row['log']), str(row['val'])) #type: ignore
