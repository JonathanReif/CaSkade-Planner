from z3 import Not, Or
import itertools
from typing import List, Dict
from smt_planning.smt.StateHandler import StateHandler
from smt_planning.dicts.CapabilityDictionary import Capability

def get_capability_mutexes(happenings: int):

    capability_dictionary = StateHandler().get_capability_dictionary()

    constraints = []

    resource_cap_combination: Dict[str, List[Capability]] = {}

    for cap in capability_dictionary.capabilities.values(): 
        resource_cap_combination.setdefault(cap.resource, [])
        resource_cap_combination[cap.resource].append(cap)

    for resource in resource_cap_combination.keys():
        combinations = list(itertools.combinations(resource_cap_combination[resource], 2))

        for happening in range(happenings):
            for combination in combinations:
                constraint = Or(Not(combination[0].occurrences[happening].z3_variable), Not(combination[1].occurrences[happening].z3_variable))
                constraints.append(constraint)

    return constraints