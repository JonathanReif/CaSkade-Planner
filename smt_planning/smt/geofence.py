from typing import Dict, List, Tuple
from z3 import Bool, And, Or, Sum, If

from smt_planning.smt.StateHandler import StateHandler
from smt_planning.dicts.PropertyDictionary import Property 

    
# class InsideGeofenceDictionary:
#     def __init__(self):
#         self.geofences = {}

#     def addInsideGeofence(self, iri:URIRef):
#         iri_string = str(iri) + "_inside"
#         self.geofences[iri_string] = Bool(iri_string)

#     def getInsideGeofenceByIri(self, iri: URIRef) -> BoolRef:
#         return self.geofences[str(iri)]
    
class Point: 
    def __init__(self, iri: str):
        self.iri = iri
        self.longitude: float
        self.latitude: float

class Geofence: 
    def __init__(self, iri: str):
        self.iri = iri
        self.points: Dict[str, Point] = {} 

    def add_point(self, point_iri: str, latitude: float = None, longitude: float = None):                           # type: ignore
        point = Point(point_iri)
        point = self.points.setdefault(point.iri, point)
        if latitude is not None:
            point.latitude = latitude
        elif longitude is not None:
            point.longitude = longitude

    def generate_geofence_polygon(self) -> List[Tuple[float, float]]:
        geofence_polygon = []
        for point in self.points.values():
            geofence_polygon.append((point.latitude, point.longitude))
        return geofence_polygon
    
class Robot: 
    def __init__(self, iri: str):
        self.iri = iri
        self.geofence = Geofence(self.iri + "/geofence")
        self.longitude: Property
        self.latitude: Property

    def add_property(self, property: Property, longitude: bool = False):
        if longitude:
            self.longitude = property
        else:
            self.latitude = property

# class GeofenceEntry: 
#     def __init__(self, inside_geofence: BoolRef, geofence: List[Tuple]):
#         self.geofence = geofence
#         self.inside_geofence = inside_geofence 

class RobotGeofenceDictionary:
    def __init__(self):
        self.robots: Dict[str, Robot] = {}

    def add_robot(self, robot_iri: str):
        self.robots[robot_iri] = Robot(robot_iri)

    def add_geofence_point(self, robot_iri: str, point_iri: str, latitude: float = None, longitude: float = None):  # type: ignore
        self.robots[robot_iri].geofence.add_point(point_iri, latitude, longitude)

#     def getGeofenceByIri(self, iri: URIRef) -> BoolRef:
#         return self.geofences[str(iri)].inside_geofence

# def get_inside_geofence_constraint(results: Result) -> InsideGeofenceDictionary:
#     geofences = InsideGeofenceDictionary()
#     for row in results: 
#         geofences.addGeofence(row.geofence)                             # type: ignore
#     return geofences
    
def get_geofence_constraints(happenings: int, event_bound: int) -> List:

    geofence_constraints = []

    query_string_geofence = """
        PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
        PREFIX RIVA: <http://www.hsu-hh.de/aut/RIVA/Logistic#>
        PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
        select ?robot ?point ?de ?type ?val where { 
            ?robot a CSS:Resource; 
                RIVA:has_Geofence ?geofence. 
            ?geofence RIVA:has_Point ?point.  
            ?point DINEN61360:has_Data_Element ?de. 
            ?de DINEN61360:has_Instance_Description ?id;
                DINEN61360:has_Type_Description ?type. 
            ?id DINEN61360:Value ?val. 
        } """
    
    query_string_vehicle_points = """
        PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
        PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
        select ?robot ?de ?type ?val where { 
            ?robot a CSS:Resource;
                DINEN61360:has_Data_Element ?de. 
            ?de DINEN61360:has_Instance_Description ?id;
                DINEN61360:has_Type_Description ?type. 
            ?id DINEN61360:Expression_Goal "Actual_Value";
                DINEN61360:Logic_Interpretation "=";
                DINEN61360:Value ?val. 
        }"""

    # Create geofence object out of query results
    query_handler = StateHandler().get_query_handler()
    results_geofence = query_handler.query(query_string_geofence) 
    gf_dict = RobotGeofenceDictionary()
    
    robots = set([str(row['robot']) for row in results_geofence])

    # Check if geofence information is available
    if not robots: 
        print("No geofence information found.")
        return geofence_constraints

    for robot in robots:
        gf_dict.add_robot(robot)
        for row in results_geofence: 
            if str(row['robot']) == robot: 
                if "longitude" in str(row['type']): 
                    longitude = float(str(row['val']))
                    gf_dict.add_geofence_point(robot, str(row['point']), longitude = longitude)
                elif "latitude" in str(row['type']): 
                    latitude = float(str(row['val']))
                    gf_dict.add_geofence_point(robot, str(row['point']), latitude = latitude)

    # Get z3 variables for property (property has to be in every happening and layer inside geofence)
    property_dictionary = StateHandler().get_property_dictionary()

    results_vehicle_props = query_handler.query(query_string_vehicle_points)
    for row in results_vehicle_props: 
        if "longitude" in str(row['type']): 
            gf_dict.robots[str(row['robot'])].add_property(property_dictionary.get_property(str(row['de'])), True)
        elif "latitude" in str(row['type']):
            gf_dict.robots[str(row['robot'])].add_property(property_dictionary.get_property(str(row['de'])))


    for robot in gf_dict.robots.values():
        # Define a list of vertices representing the polygon
        geofence_polygon = robot.geofence.generate_geofence_polygon()

        # get z3 variables for longitude and latitude
        for happening in range(happenings):
            for layer in range(event_bound):
                z3_variable_latitude = robot.latitude.occurrences[happening][layer].z3_variable
                z3_variable_longitude = robot.longitude.occurrences[happening][layer].z3_variable

                # Create symbolic boolean variables for the edges crossed by the ray
                crossed_edges = [Bool(f'crossed_edge_{i}') for i in range(len(geofence_polygon))]

                # Add constraints to check if the point is inside the polygon
                for i in range(len(geofence_polygon)):
                    p1x, p1y = geofence_polygon[i]
                    p2x, p2y = geofence_polygon[(i + 1) % len(geofence_polygon)]
                    
                    # Check if the ray crosses this edge
                    cross_condition = And(
                        z3_variable_longitude > min(p1y, p2y),                                                          # type: ignore
                        z3_variable_longitude <= max(p1y, p2y),                                                         # type: ignore
                        z3_variable_latitude <= max(p1x, p2x),                                                          # type: ignore
                        p1y != p2y,
                        Or(
                            p1x == p2x,
                            z3_variable_latitude <= (z3_variable_longitude - p1y) * (p2x - p1x) / (p2y - p1y) + p1x     # type: ignore
                        )
                    )

                    # Add constraint 
                    constraint = crossed_edges[i] == cross_condition
                    geofence_constraints.append(constraint) 

                # Check if an odd number of edges are crossed
                num_crossed_edges = Sum([If(ce, 1, 0) for ce in crossed_edges])
                inside = num_crossed_edges % 2 == 1
                geofence_constraints.append(inside)

    return geofence_constraints
