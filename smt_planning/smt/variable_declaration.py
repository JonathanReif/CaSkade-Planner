from smt_planning.smt.StateHandler import StateHandler


def create_property_dictionary_with_occurrences(happenings:int, event_bound:int) -> None:
	stateHandler = StateHandler()	
	property_dictionary = stateHandler.get_property_dictionary()
	property_dictionary.add_property_occurrences(happenings, event_bound)

def create_capability_dictionary_with_occurrences(happenings:int) -> None:
	capability_dictionary = StateHandler().get_capability_dictionary()
	capability_dictionary.add_capability_occurrences(happenings)
	