from smt_planning.smt.StateHandler import StateHandler
from smt_planning.dicts.GeofenceDictionary import RobotGeofenceDictionary

def get_geofence_constraints() -> RobotGeofenceDictionary:

    query_string_geofence = """
        PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
        PREFIX RIVA: <http://www.hsu-hh.de/aut/RIVA/Logistic#>
        PREFIX DINEN61360: <http://www.w3id.org/hsu-aut/DINEN61360#>
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
        PREFIX DINEN61360: <http://www.w3id.org/hsu-aut/DINEN61360#>
        select ?robot ?de ?type where { 
            ?robot a CSS:Resource;
                DINEN61360:has_Data_Element ?de. 
            ?de DINEN61360:has_Type_Description ?type. 
            FILTER(CONTAINS(LCASE(STR(?type)), "latitude") || CONTAINS(LCASE(STR(?type)), "longitude"))
        }"""

    # Create geofence object out of query results
    query_handler = StateHandler().get_query_handler()
    results_geofence = query_handler.query(query_string_geofence) 
    gf_dict = RobotGeofenceDictionary()
    
    robots = set([str(row['robot']) for row in results_geofence])

    # Check if geofence information is available
    if not robots: 
        print("No geofence information found.")
        return gf_dict

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

    return gf_dict