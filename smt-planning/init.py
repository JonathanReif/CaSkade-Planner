from rdflib import Graph
from z3 import Not
from dicts.PropertyDictionary import PropertyDictionary

def get_init(graph: Graph, property_dictionary: PropertyDictionary):
	
	'''
	Get initial state properties by checking the values of all Actual_Value instances
	'''
	sparql_string = """
		PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
		PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
		PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
		PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
		SELECT DISTINCT ?de ?log ?val WHERE { 
			?de a DINEN61360:Data_Element.
			?de DINEN61360:has_Instance_Description ?id.
			?id DINEN61360:Expression_Goal "Actual_Value";
				DINEN61360:Logic_Interpretation ?log;
				DINEN61360:Value ?val. 
		} """

	# Inits 
	results = graph.query(sparql_string)
	inits = []
	for row in results:
		property = property_dictionary.get_property(str(row.de), 0, 0).z3_variable					
		relation = str(row.log)															
		value = str(row.val)														    
		
		prop_type = property_dictionary.get_property_data_type(str(row.de)) 
		if prop_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":

			match relation:
				case "<":
					init = property < value
				case "<=":
					init = property <= value
				case "=":
					init = property == value
				case "!=":
					init = property != value
				case ">=":
					init = property >= value
				case ">":
					init = property > value
				case _:
					raise RuntimeError("Incorrent logical relation")
			inits.append(init)

		elif prop_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
			match value: 
				case 'true':
					init = property
				case 'false':
					init = Not(property)
				case _:
					raise RuntimeError("Incorrect value for Boolean")
				
			inits.append(init)
	
	return inits