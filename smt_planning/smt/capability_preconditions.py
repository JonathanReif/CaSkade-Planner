from typing import List
from z3 import Implies, BoolRef, Not

from smt_planning.smt.StateHandler import StateHandler

def capability_preconditions_smt(happenings: int, event_bound: int) -> List[BoolRef]:
	property_dictionary = StateHandler().get_property_dictionary()
	capability_dictionary = StateHandler().get_capability_dictionary()
	preconditions_smt = []
	for happening in range(happenings):
		for precondition in property_dictionary.get_preconditions().values():
			currentCap = capability_dictionary.get_capability_occurrence(precondition.cap_iri, happening).z3_variable
			currentProp = property_dictionary.get_provided_property_occurrence(precondition.iri, happening, 0).z3_variable																							

			prop_type = property_dictionary.get_property_data_type(precondition.iri) 
			if prop_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":

				match precondition.logical_relation:
					case "<":
						precondition_smt = Implies(currentCap, currentProp < precondition.value) # type: ignore
					case "<=":
						precondition_smt = Implies(currentCap, currentProp <= precondition.value) # type: ignore
					case "=":
						precondition_smt = Implies(currentCap, currentProp == precondition.value)
					case "!=":
						precondition_smt = Implies(currentCap, currentProp != precondition.value)
					case ">=":
						precondition_smt = Implies(currentCap, currentProp >= precondition.value) # type: ignore
					case ">":
						precondition_smt = Implies(currentCap, currentProp > precondition.value) # type: ignore
					case _:
						raise RuntimeError("Incorrect logical relation")
				
				preconditions_smt.append(precondition_smt)
			elif prop_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Boolean":
				match precondition.value: 
					case 'true':
						precondition_smt = Implies(currentCap, currentProp)
					case 'false':
						precondition_smt = Implies(currentCap, Not(currentProp))
					case _:
						raise RuntimeError("Incorrect value for Boolean")
					
				preconditions_smt.append(precondition_smt)
	return preconditions_smt


