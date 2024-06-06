from smt_planning.smt.StateHandler import StateHandler
from smt_planning.dicts.PropertyDictionary import CapabilityType

def get_init_and_goal():
	
	query_string = """
		PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
		PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
		PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
		PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
		SELECT DISTINCT ?de ?capType ?expr_goal ?log ?val WHERE {
			?cap a ?capType; 
				^CSS:requiresCapability ?process.
			?process ?relation ?inout.
			
			values ?capType { CaSk:ProvidedCapability CaSk:RequiredCapability }.	
			VALUES ?relation {VDI3682:hasInput VDI3682:hasOutput}.
			{
			?de a DINEN61360:Data_Element.
			?de DINEN61360:has_Instance_Description ?id.
			?id DINEN61360:Expression_Goal ?expr_goal; 
				DINEN61360:Logic_Interpretation ?log;
				DINEN61360:Value ?val. 
				FILTER (?expr_goal = "Actual_Value")
			?de DINEN61360:has_Instance_Description ?id2. 
			?inout VDI3682:isCharacterizedBy ?id2.
			}
			UNION {
				?cap a  CaSk:RequiredCapability. 
				?process VDI3682:hasOutput ?inout. 
				?inout VDI3682:isCharacterizedBy ?id.
				?de DINEN61360:has_Instance_Description ?id.
				?id DINEN61360:Expression_Goal ?expr_goal;
					DINEN61360:Logic_Interpretation ?log;
					DINEN61360:Value ?val. 
				FILTER (?expr_goal = "Requirement")
			}
		} """
	stateHandler = StateHandler()
	query_handler = stateHandler.get_query_handler()
	property_dictionary = stateHandler.get_property_dictionary()
	results = query_handler.query(query_string)
	for row in results:
		# caps = list(row['caps'].split(","))
		if str(row['capType']) == "http://www.w3id.org/hsu-aut/cask#ProvidedCapability":
			property_dictionary.add_instance_description(str(row['de']), "", CapabilityType.ProvidedCapability, str(row['expr_goal']), str(row['log']), str(row['val']))
		elif str(row['capType']) == "http://www.w3id.org/hsu-aut/cask#RequiredCapability":
			property_dictionary.add_instance_description(str(row['de']), "", CapabilityType.RequiredCapability, str(row['expr_goal']), str(row['log']), str(row['val'])) 
		else:
			raise RuntimeError("Incorrect capability type")