from smt_planning.smt.StateHandler import StateHandler

def get_capability_preconditions_and_effects():
	query_string = """
	PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>

	SELECT ?cap ?de ?expr_goal ?log ?val WHERE { 
		?cap a CaSk:ProvidedCapability;
			^CSS:requiresCapability ?process.
		?process VDI3682:hasInput|VDI3682:hasOutput ?input.
		?input VDI3682:isCharacterizedBy ?id.
		?id DINEN61360:Expression_Goal ?expr_goal; 
			DINEN61360:Logic_Interpretation ?log;
			DINEN61360:Value ?val.
		Values ?expr_goal {"Requirement" "Assurance"}.
		?de DINEN61360:has_Instance_Description ?id.
	}
	"""
	stateHandler = StateHandler()
	query_handler = stateHandler.get_query_handler()
	property_dictionary = stateHandler.get_property_dictionary()
	results = query_handler.query(query_string)
	for row in results:
		property_dictionary.add_instance_description(str(row['de']), str(row['cap']), str(row['expr_goal']), str(row['log']), str(row['val'])) #type: ignore

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
