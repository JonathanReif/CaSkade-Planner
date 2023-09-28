from typing import List

from smt_planning.dicts.PropertyDictionary import PropertyDictionary
from smt_planning.StateHandler import StateHandler


def get_real_variable_continuous_changes(happenings: int, event_bound: int) -> List:
	continuous_changes = []

	property_dictionary = StateHandler().get_property_dictionary()
	properties = property_dictionary.provided_properties.values()

	for happening in range(happenings)[1:]:
		for property in properties:
			if property.data_type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":
				property_current_happening_start = property.occurrences[happening][0].z3_variable
				property_last_happening_end = property.occurrences[happening-1][event_bound-1].z3_variable
				
				# Track change between happenings, so that no random change is possible
				continuous_change = property_current_happening_start == property_last_happening_end
				continuous_changes.append(continuous_change)
	return continuous_changes