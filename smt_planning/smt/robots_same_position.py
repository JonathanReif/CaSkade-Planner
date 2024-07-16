from z3 import Or

from smt_planning.smt.StateHandler import StateHandler

def robot_positions_smt(happenings: int, event_bound: int):

    stateHandler = StateHandler()
    property_dictionary = stateHandler.get_property_dictionary()
    geofence_dictionary = stateHandler.get_geofence_dictionary()
    robots_not_same_position_constraints = []
    lat_props = []
    long_props = []

    for robot in geofence_dictionary.robots.values():
        lat_props.append(robot.latitude.iri)
        long_props.append(robot.longitude.iri)
    
    for happening in range(happenings):
        for event in range(event_bound):
            for i in range(len(lat_props) - 1): 
                lat_0 = property_dictionary.get_provided_property_occurrence(lat_props[i], happening, event).z3_variable
                long_0 = property_dictionary.get_provided_property_occurrence(long_props[i], happening, event).z3_variable
                for j in range(i + 1, len(lat_props)):
                    lat_1 = property_dictionary.get_provided_property_occurrence(lat_props[j], happening, event).z3_variable
                    long_1 = property_dictionary.get_provided_property_occurrence(long_props[j], happening, event).z3_variable
                    robots_not_same_position = Or(lat_0 != lat_1, long_0 != long_1)
                    robots_not_same_position_constraints.append(robots_not_same_position)

    return robots_not_same_position_constraints