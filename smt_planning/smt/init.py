from z3 import Not

from smt_planning.smt.StateHandler import StateHandler
from smt_planning.smt.property_links import get_related_properties

def init_smt():
	property_dictionary = StateHandler().get_property_dictionary()
	inits = []
	for init_property_iri, init_value_expressions in property_dictionary.get_inits().items():
		
		# Every init may consist of multiple value expressions (e.g., init > 5 , init <= 10). Create assertions for every init expression
		for init_expression in init_value_expressions:
			init_property_z3_var = property_dictionary.get_property_occurence(init_property_iri, 0, 0).z3_variable
			relation = init_expression.logical_interpretation															
			value = init_expression.value														    
		
			prop_type = property_dictionary.get_property_data_type(init_property_iri) 
			if prop_type == "http://www.w3id.org/hsu-aut/DINEN61360#Real" or prop_type == "http://www.w3id.org/hsu-aut/DINEN61360#Integer":

				match relation:
					case "<":
						init_smt = init_property_z3_var < value # type: ignore
					case "<=":
						init_smt = init_property_z3_var <= value # type: ignore
					case "=":
						init_smt = init_property_z3_var == value 
					case "!=":
						init_smt = init_property_z3_var != value 
					case ">=":
						init_smt = init_property_z3_var >= value # type: ignore
					case ">":
						init_smt = init_property_z3_var > value # type: ignore
					case _:
						raise RuntimeError("Incorrent logical relation")
				inits.append(init_smt)

			elif prop_type == "http://www.w3id.org/hsu-aut/DINEN61360#Boolean":
				match value: 
					case 'true':
						init_smt = init_property_z3_var
					case 'false':
						init_smt = Not(init_property_z3_var)
					case _:
						raise RuntimeError("Incorrect value for Boolean")
					
				inits.append(init_smt)

		# Handle related properties of every init property defined by a required cap 
		# Important: Ignore inits defined by actual values, i.e. configuration of provided caps. 
		# These values will be imposed on product properties once the corresponding capabilities are executed, but cannot be related to properties before that.
		if not(property_dictionary.get_property(init_property_iri) in property_dictionary.required_properties.values()): continue
		
		related_properties = get_related_properties(str(init_property_iri))
		for related_property in related_properties:
			if (related_property.relation_type == "Output" or all(instance.expr_goal == 'Actual_Value' for instance in related_property.instances)): continue
			try: 
				related_property_z3_var = property_dictionary.get_provided_property_occurrence(str(related_property.iri), 0, 0).z3_variable
				relation_constraint = (related_property_z3_var == init_property_z3_var)
				inits.append(relation_constraint)
			except KeyError:
				print(f"While creating inits, there was no provided property with key {related_property.iri}.")
	
	return inits