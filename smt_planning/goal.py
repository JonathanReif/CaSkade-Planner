from rdflib import Graph
from z3 import Implies, Not
from dicts.PropertyDictionary import PropertyDictionary

def get_goal(graph:Graph, property_dictionary: PropertyDictionary, happenings):

	query_string = """
		PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
		PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
		PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
		PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
		SELECT ?de ?log ?val WHERE { 
			?cap a CaSk:RequiredCapability;
			^CSS:requiresCapability ?process.
			?process VDI3682:hasOutput ?out.
			?out VDI3682:isCharacterizedBy ?id.
			?de DINEN61360:has_Instance_Description ?id.
			?id DINEN61360:Expression_Goal "Requirement";
				DINEN61360:Logic_Interpretation ?log;
				DINEN61360:Value ?val. 
		} """

	results = graph.query(query_string)
	goals = []
	for row in results:
		property = property_dictionary.get_required_property_occurrence(str(row.de)).z3_variable					
		relation = str(row.log)															
		value = str(row.val)                                                            
		
		prop_type = property_dictionary.get_property_data_type(str(row.de)) 
		if prop_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":

			match relation:														    
				case "<":
					goal = property < value
				case "<=":
					goal = property <= value
				case "=":
					goal = property == value
				case "!=":
					goal = property != value
				case ">=":
					goal = property >= value
				case ">":
					goal = property > value
				case _:
					raise RuntimeError("Incorrent logical relation")
			goals.append(goal)
		
		elif prop_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
				match value: 
					case 'true':
						goal = property
					case 'false':
						goal = Not(property)
					case _:
						raise RuntimeError("Incorrect value for Boolean")
					
				goals.append(goal)
		
	return goals