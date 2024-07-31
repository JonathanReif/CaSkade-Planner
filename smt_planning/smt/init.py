from z3 import Not

from smt_planning.smt.StateHandler import StateHandler

def init_smt():
	property_dictionary = StateHandler().get_property_dictionary()
	inits = []
	for init in property_dictionary.get_inits().values():
		property_iri = init.iri
		property = property_dictionary.get_property_occurence(property_iri, 0, 0).z3_variable					
		relation = init.logical_interpretation															
		value = init.value														    
	
		prop_type = property_dictionary.get_property_data_type(property_iri) 
		if prop_type == "http://www.w3id.org/hsu-aut/DINEN61360#Real" or prop_type == "http://www.w3id.org/hsu-aut/DINEN61360#Integer":

			match relation:
				case "<":
					init_smt = property < value # type: ignore
				case "<=":
					init_smt = property <= value # type: ignore
				case "=":
					init_smt = property == value 
				case "!=":
					init_smt = property != value 
				case ">=":
					init_smt = property >= value # type: ignore
				case ">":
					init_smt = property > value # type: ignore
				case _:
					raise RuntimeError("Incorrent logical relation")
			inits.append(init_smt)

		elif prop_type == "http://www.w3id.org/hsu-aut/DINEN61360#Boolean":
			match value: 
				case 'true':
					init_smt = property
				case 'false':
					init_smt = Not(property)
				case _:
					raise RuntimeError("Incorrect value for Boolean")
				
			inits.append(init_smt)
	
	return inits