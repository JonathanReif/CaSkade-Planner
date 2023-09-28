from rdflib import Graph
from z3 import Not, Or
import itertools
from typing import List
from smt_planning.dicts.CapabilityDictionary import CapabilityDictionary, Capability

def get_capability_mutexes(graph: Graph, capability_dictionary: CapabilityDictionary, happenings):

    query_string = """
        PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
        PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>

        SELECT ?res (GROUP_CONCAT(?cap; separator=", ") as ?caps) WHERE {  
            ?res CSS:providesCapability ?cap. 
            ?cap a CaSk:ProvidedCapability.
        } GROUP BY ?res """
    result = graph.query(query_string)

    constraints = []

    for row in result: 
        caps = set(row.caps.split(", "))
        capabilities: List[Capability] = []
        for cap in caps:
            capability = capability_dictionary.get_capability(cap)
            capabilities.append(capability)

        combinations = list(itertools.combinations(capabilities, 2))

        for happening in range(happenings):
            for combination in combinations:
                constraint = Or(Not(combination[0].occurrences[happening].z3_variable), Not(combination[1].occurrences[happening].z3_variable))
                constraints.append(constraint)

    return constraints