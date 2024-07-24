from z3 import Not

from smt_planning.smt.StateHandler import StateHandler

def goal_smt():
	property_dictionary = StateHandler().get_property_dictionary()
	goals = []
	for goal in property_dictionary.get_goals().values():
		property_iri = goal.iri
		property = property_dictionary.get_required_property_occurrence(property_iri).z3_variable					
		relation = goal.logical_interpretation															
		value = goal.value                                                            
		
		prop_type = property_dictionary.get_property_data_type(property_iri) 
		if prop_type == "http://www.w3id.org/hsu-aut/DINEN61360#Real" or prop_type == "http://www.w3id.org/hsu-aut/DINEN61360#Integer":

			match relation:														    
				case "<":
					goal_smt = property < value # type: ignore
				case "<=":
					goal_smt = property <= value # type: ignore
				case "=":
					goal_smt = property == value
				case "!=":
					goal_smt = property != value
				case ">=":
					goal_smt = property >= value # type: ignore
				case ">":
					goal_smt = property > value # type: ignore
				case _:
					raise RuntimeError("Incorrent logical relation")
			goals.append(goal_smt)
		
		elif prop_type == "http://www.w3id.org/hsu-aut/DINEN61360#Boolean":
				match value: 
					case 'true':
						goal_smt = property
					case 'false':
						goal_smt = Not(property)
					case _:
						raise RuntimeError("Incorrect value for Boolean")
					
				goals.append(goal_smt)
		
	return goals