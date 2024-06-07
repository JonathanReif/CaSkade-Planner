from z3 import Or

from smt_planning.smt.StateHandler import StateHandler

def robot_positions_smt(happenings: int, event_bound: int):

    stateHandler = StateHandler()
    property_dictionary = stateHandler.get_property_dictionary()
    geofence_dictionary = stateHandler.get_geofence_dictionary()
    robots_not_same_position_constraints = []
    lat_props = []
    long_props = []

    for happening in range(happenings):
        for event in range(event_bound):
            for robot in geofence_dictionary.robots.values():
                lat1 = property_dictionary.get_provided_property_occurrence(robot.latitude.iri, happening, event).z3_variable
                long1 = property_dictionary.get_provided_property_occurrence(robot.longitude.iri, happening, event).z3_variable
                lat_props.append(lat1)
                long_props.append(long1)

            for i in range(len(lat_props) - 1): 
                robots_not_same_position = Or(lat_props[i] != lat_props[i+1], long_props[i] != long_props[i+1])
                robots_not_same_position_constraints.append(robots_not_same_position)

    return robots_not_same_position_constraints