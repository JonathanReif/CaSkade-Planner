from rdflib import Graph
from dicts.PropertyDictionary import PropertyDictionary

def get_init(graph: Graph, property_dictionary: PropertyDictionary):
    
    '''
    Get initial state properties
    Check for Outputs because resource can have actual value for required output (e.g. longitude)
    '''
    sparql_string = """
        PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
        PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
        PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
        PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
        SELECT DISTINCT ?de ?log ?val WHERE { 
            ?cap a CaSk:RequiredCapability;
            ^CSS:requiresCapability ?process.
            ?process VDI3682:hasInput|VDI3682:hasOutput ?inout.
            ?inout VDI3682:isCharacterizedBy ?id.
            ?de DINEN61360:has_Instance_Description ?id.
            ?de DINEN61360:has_Instance_Description ?id_any.
            ?id_any DINEN61360:Expression_Goal "Actual_Value";
                DINEN61360:Logic_Interpretation ?log;
                DINEN61360:Value ?val. 
        } """

    # Inits 
    results = graph.query(sparql_string)
    inits = []
    for row in results:
        property = property_dictionary.getPropertyVariable(row.de, 0, 0)				# type: ignore
        relation = str(row.log)															# type: ignore
        value = str(row.val)														    # type: ignore
        match relation:
            case "<":
                init = property < value
            case "<=":
                init = property <= value
            case "=":
                init = property == value
            case "!=":
                init = property != value
            case ">=":
                init = property >= value
            case ">":
                init = property > value
            case _:
                raise RuntimeError("Incorrent logical relation")
        inits.append(init)	
    return inits										