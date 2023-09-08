from dicts.PropertyDictionary import PropertyDictionary
from typing import List

def get_real_variable_continous_changes(property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List:
	continous_changes = []
	for happening in range(happenings)[1:]:
		for property in property_dictionary.properties.values():
			if property.type == "http://www.hsu-ifa.de/ontologies/DINEN61360#Real":
				property_current_happening_start = property.states[happening][0]
				property_last_happening_end = property.states[happening-1][event_bound-1]
				
				# Track change between happenings, so that no random change is possible
				continous_change = property_current_happening_start == property_last_happening_end
				continous_changes.append(continous_change)
	return continous_changes