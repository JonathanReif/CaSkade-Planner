from typing import List
from z3 import Bool, And, Or, Sum, If, BoolRef

from smt_planning.smt.StateHandler import StateHandler

def geofence_smt(happenings: int, event_bound: int) -> List[BoolRef]:

    stateHandler = StateHandler()
    gf_dict = stateHandler.get_geofence_dictionary()

    geofence_constraints = []
    robot_id = 1

    for robot in gf_dict.robots.values():
        # Define a list of vertices representing the polygon
        geofence_polygon = robot.geofence.generate_geofence_polygon()

        # get z3 variables for longitude and latitude
        for happening in range(happenings):
            for layer in range(event_bound):
                z3_variable_latitude = robot.latitude.occurrences[happening][layer].z3_variable
                z3_variable_longitude = robot.longitude.occurrences[happening][layer].z3_variable

                # Create symbolic boolean variables for the edges crossed by the ray
                crossed_edges = [Bool(f'crossed_edge_{robot_id}_{i}_{happening}_{layer}') for i in range(len(geofence_polygon))]

                # Add constraints to check if the point is inside the polygon
                for i in range(len(geofence_polygon)):
                    p1x, p1y = geofence_polygon[i]
                    p2x, p2y = geofence_polygon[(i + 1) % len(geofence_polygon)]
                    
                    # Check if the ray crosses this edge
                    cross_condition = And(
                        z3_variable_latitude > min(p1y, p2y),                                                          # type: ignore
                        z3_variable_latitude <= max(p1y, p2y),                                                         # type: ignore
                        z3_variable_longitude <= max(p1x, p2x),                                                          # type: ignore
                        p1y != p2y,
                        Or(
                            p1x == p2x,
                            z3_variable_longitude <= (z3_variable_latitude - p1y) * (p2x - p1x) / (p2y - p1y) + p1x     # type: ignore
                        )
                    )

                    # Add constraint 
                    constraint = crossed_edges[i] == cross_condition
                    geofence_constraints.append(constraint) 

                # Check if an odd number of edges are crossed
                num_crossed_edges = Sum([If(ce, 1, 0) for ce in crossed_edges])
                inside = num_crossed_edges % 2 == 1
                geofence_constraints.append(inside)

        robot_id += 1
    return geofence_constraints
