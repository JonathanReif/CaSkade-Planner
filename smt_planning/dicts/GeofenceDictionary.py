from typing import Dict, List, Tuple
from smt_planning.dicts.PropertyDictionary import Property
    
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

class RobotGeofenceDictionary:
    def __init__(self):
        self.robots: Dict[str, Robot] = {}

    def add_robot(self, robot_iri: str):
        self.robots[robot_iri] = Robot(robot_iri)

    def add_geofence_point(self, robot_iri: str, point_iri: str, latitude: float = None, longitude: float = None):  # type: ignore
        self.robots[robot_iri].geofence.add_point(point_iri, latitude, longitude)