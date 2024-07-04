from z3 import Not, Or
import itertools
from typing import List, Dict
from smt_planning.smt.StateHandler import StateHandler
from smt_planning.dicts.CapabilityDictionary import Capability

def get_capability_mutexes(happenings: int):

    resource_dictionary = StateHandler().get_resource_dictionary()

    constraints = []

    for res in resource_dictionary.resources.values(): 
        combinations = list(itertools.combinations(res.capabilities, 2))

        for happening in range(happenings):
            for combination in combinations:
                constraint = Or(Not(combination[0].occurrences[happening].z3_variable), Not(combination[1].occurrences[happening].z3_variable))
                constraints.append(constraint)

    return constraints