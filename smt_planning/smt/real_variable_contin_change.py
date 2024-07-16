from typing import List

from smt_planning.dicts.PropertyDictionary import PropertyDictionary, FreeVariable
from smt_planning.smt.StateHandler import StateHandler


def get_real_variable_continuous_changes(happenings: int, event_bound: int) -> List:
	continuous_changes = []

	property_dictionary = StateHandler().get_property_dictionary()
	properties = property_dictionary.provided_properties.values()

	for happening in range(happenings)[1:]:
		for property in properties:
			if property.data_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real" or property.data_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Integer":
				free_variable = False
				for instance in property.instances.values():
					if isinstance(instance, FreeVariable):
						free_variable = True
						continue
					else:
						free_variable = False
						break
				if free_variable:
					continue
				property_current_happening_start = property.occurrences[happening][0].z3_variable
				property_last_happening_end = property.occurrences[happening-1][event_bound-1].z3_variable
				
				# Track change between happenings, so that no random change is possible
				continuous_change = property_current_happening_start == property_last_happening_end
				continuous_changes.append(continuous_change)
	return continuous_changes