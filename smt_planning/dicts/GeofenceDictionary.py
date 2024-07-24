from typing import Dict, List, Tuple
from smt_planning.dicts.PropertyDictionary import Property
    
class Point: 
    def __init__(self, iri: str):
        self.iri = iri
        self.longitude: float
        self.latitude: float

class Area: 
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

    def generate_polygon(self) -> List[Tuple[float, float]]:
        polygon = []
        for point in self.points.values():
            polygon.append((point.longitude, point.latitude))
        return polygon
    
class Geofence(Area):
    def __init__(self, iri: str):
        super().__init__(iri)

class Gozone(Area): 
    def __init__(self, iri: str):
        super().__init__(iri)
        self.holes: Dict[str, Area] = {}
        self.alternative_gozones: Dict[str, Area] = {}

    def add_hole(self, iri: str):
        hole = Area(iri)
        self.holes.setdefault(iri, hole)

    def add_alternative_gozone(self, iri: str):
        alt_gozone = Area(iri)
        self.alternative_gozones.setdefault(iri, alt_gozone)
    
    def add_hole_point(self, hole_iri: str, point_iri: str, latitude: float = None, longitude: float = None):   # type: ignore
        self.holes[hole_iri].add_point(point_iri, latitude, longitude)

    def add_alternative_gozone_point(self, alt_gozone_iri: str, point_iri: str, latitude: float = None, longitude: float = None): # type: ignore
        self.alternative_gozones[alt_gozone_iri].add_point(point_iri, latitude, longitude)

class Robot: 
    def __init__(self, iri: str):
        self.iri = iri
        self.geofence = Geofence(self.iri + "/geofence")
        self.gozone = Gozone(self.iri + "/gozone") 
        self.longitude: Property
        self.latitude: Property

    def add_property(self, property: Property, longitude: bool = False):
        if longitude:
            self.longitude = property
        else:
            self.latitude = property
    
    def get_iri(self) -> str:
        return self.iri
    
    def get_gozone(self) -> Gozone:
        return self.gozone
    

class RobotGeofenceDictionary:
    def __init__(self):
        self.robots: Dict[str, Robot] = {}

    def add_robot(self, robot_iri: str):
        self.robots[robot_iri] = Robot(robot_iri)

    def add_geofence_point(self, robot_iri: str, point_iri: str, latitude: float = None, longitude: float = None):  # type: ignore
        self.robots[robot_iri].geofence.add_point(point_iri, latitude, longitude)

    def get_robots(self) -> Dict[str, Robot]:
        return self.robots