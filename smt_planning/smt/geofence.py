from typing import Dict, List, Tuple
from z3 import Bool, BoolRef, And
from rdflib import URIRef, Graph
from rdflib.query import Result

from smt_planning.smt.StateHandler import StateHandler

    
class InsideGeofenceDictionary:
    def __init__(self):
        self.geofences = {}

    def addInsideGeofence(self, iri:URIRef):
        iri_string = str(iri) + "_inside"
        self.geofences[iri_string] = Bool(iri_string)

    def getInsideGeofenceByIri(self, iri: URIRef) -> BoolRef:
        return self.geofences[str(iri)]
    
class Point: 
    def __init__(self, iri: str):
        self.iri = iri
        self.longitude: float
        self.latitude: float

class Geofence: 
    def __init__(self, iri: str):
        self.iri = iri
        self.points: Dict[str, Point] = {} 

    def add_point(self, point_iri: str, latitude: float = 0, longitude: float = 0):
        point = Point(point_iri)
        point = self.points.setdefault(point.iri, point)
        if latitude != 0:
            point.latitude = latitude
        elif longitude != 0:
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
        self.position = Point(self.iri + "/position")

    def add_position(self, latitude: float = 0, longitude: float = 0):
        if latitude != 0:
            self.position.latitude = latitude
        elif longitude != 0:
            self.position.longitude = longitude

# class GeofenceEntry: 
#     def __init__(self, inside_geofence: BoolRef, geofence: List[Tuple]):
#         self.geofence = geofence
#         self.inside_geofence = inside_geofence 

class RobotGeofenceDictionary:
    def __init__(self):
        self.robots: Dict[str, Robot] = {}

    def add_robot(self, robot_iri: str):
        self.robots[robot_iri] = Robot(robot_iri)

    def add_robot_position(self, robot_iri: str, latitude: float = 0, longitude: float = 0):
        self.robots[robot_iri].add_position(latitude, longitude)

    def add_geofence_point(self, robot_iri: str, point_iri: str, latitude: float = 0, longitude: float = 0):
        self.robots[robot_iri].geofence.add_point(point_iri, latitude, longitude)

#     def getGeofenceByIri(self, iri: URIRef) -> BoolRef:
#         return self.geofences[str(iri)].inside_geofence

# def get_inside_geofence_constraint(results: Result) -> InsideGeofenceDictionary:
#     geofences = InsideGeofenceDictionary()
#     for row in results: 
#         geofences.addGeofence(row.geofence)                             # type: ignore
#     return geofences
    
def get_geofence_constraints():

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

    query_handler = StateHandler().get_query_handler()
    results_geofence = query_handler.query(query_string_geofence) 
    gf_dict = RobotGeofenceDictionary()
    
    robots = set([str(row['robot']) for row in results_geofence])
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

    results_vehicle_props = query_handler.query(query_string_vehicle_points)
    for row in results_vehicle_props: 
        if "longitude" in str(row['type']): 
            longitude = float(str(row['val']))
            gf_dict.add_robot_position(str(row['robot']), longitude = longitude)
        elif "latitude" in str(row['type']): 
            latitude = float(str(row['val']))
            gf_dict.add_robot_position(str(row['robot']), latitude = latitude)


    # for geofence in gf_dict.geofences.values():
    #     geofence_polygon = geofence.generate_geofence_polygon()
    #     crossed_edges = [Bool(f'crossed_edge_{i}') for i in range(len(geofence_polygon))]
    #     # Add constraints to check if the point is inside the polygon
    #     for i in range(len(geofence_polygon)):
    #         p1x, p1y = geofence_polygon[i]
    #         p2x, p2y = geofence_polygon[(i + 1) % len(geofence_polygon)]
            
    #         # Check if the ray crosses this edge
    #         cross_condition = And(
    #             Rover7_longitude70_0_0 > min(p1y, p2y),
    #             Rover7_longitude70_0_0 <= max(p1y, p2y),
    #             Rover7_lattitude71_0_0 <= max(p1x, p2x),
    #             p1y != p2y,
    #             Or(
    #                 p1x == p2x,
    #                 Rover7_lattitude71_0_0 <= (Rover7_longitude70_0_0 - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
    #             )
    #         )




    # inside_geofence_dictionary = get_inside_geofence_constraint(results_geofence)

    # geofence_constraints = []

    # # every bool for geofence has to be true, so that every point of a robot is inside geofence  
    # for geofence in inside_geofence_dictionary.geofences: 
    #     inside_geofence_constraint = geofence
    #     geofence_constraints.append(inside_geofence_constraint)

    # for row in results_geofence: 
    #     geofence = Geofence(str(row.geofence))          # type: ignore
    #     points_result = row.points.split(', ')           # type: ignore 
    #     points = []
    #     for point in points_result:                    # type: ignore
    #         geofence.add_point(row.point)                # type: ignore
        


    

    # # Variable for geofence of resource -- nicht veränderlich zur Laufzeit 
    # Rover7_geofence: List[Tuple[float, float]] = [(53.56713503872737, 10.11185556650162),(53.56666495361132, 10.111909210681915),(53.56667929526839, 10.112668275833132),(53.56716372171786, 10.112611949443817), (53.56713503872737, 10.11185556650162)]

    # # Constraints for resources (Geofence) 
    # # Rover7_within_geofence_0_0 = Bool('kdkddkdkdk')
    # # Rover7_within_geofence_0_0 = cc.within_geofence(Rover7_lattitude71_0_0, Rover7_longitude70_0_0, Rover7_geofence)
    # # solver.add(Rover7_inside_geofence == Rover7_within_geofence_0_0)
    

    # crossed_edges = [Bool(f'crossed_edge_{i}') for i in range(len(Rover7_geofence))]

    # # Add constraints to check if the point is inside the polygon
    # for i in range(len(Rover7_geofence)):
    #     p1x, p1y = Rover7_geofence[i]
    #     p2x, p2y = Rover7_geofence[(i + 1) % len(Rover7_geofence)]
        
    #     # Check if the ray crosses this edge
    #     cross_condition = And(
    #         Rover7_longitude70_0_0 > min(p1y, p2y),
    #         Rover7_longitude70_0_0 <= max(p1y, p2y),
    #         Rover7_lattitude71_0_0 <= max(p1x, p2x),
    #         p1y != p2y,
    #         Or(
    #             p1x == p2x,
    #             Rover7_lattitude71_0_0 <= (Rover7_longitude70_0_0 - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
    #         )
    #     )

    #     # Add a constraint that records if the ray crosses this edge
    #     solver.add(crossed_edges[i] == cross_condition)

    # # Check if an odd number of edges are crossed
    # num_crossed_edges = Sum([If(ce, 1, 0) for ce in crossed_edges])
    # inside = num_crossed_edges % 2 == 1

    # # Add the inside constraint to the solver
    # solver.add(Rover7_inside_geofence == inside)