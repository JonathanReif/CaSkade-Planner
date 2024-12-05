from z3 import Not, Or
import itertools
from typing import Set, List
from smt_planning.smt.StateHandler import StateHandler
from smt_planning.dicts.PropertyDictionary import Property
from smt_planning.dicts.CapabilityDictionary import CapabilityPropertyInfluence
from smt_planning.smt.property_links import get_related_properties

def get_capability_mutexes(happenings: int):

	resource_dictionary = StateHandler().get_resource_dictionary()

	constraints = []

	for res in resource_dictionary.resources.values(): 
		combinations = list(itertools.combinations(res.capabilities, 2))

		for happening in range(happenings):
			for combination in combinations:
				constraint = Or(Not(combination[0].occurrences[happening].z3_variable), Not(combination[1].occurrences[happening].z3_variable))
				constraints.append(constraint)
				

	
	capability_mutex_tuples: Set[CapabilityTuple] = set()
	capability_dictionary = StateHandler().get_capability_dictionary()
	capabilities  = capability_dictionary.provided_capabilities.values()
	for cap in capabilities:
		cap_input_properties = cap.input_properties
		cap_input_and_related: List[Property] = [*cap_input_properties]
		[cap_input_and_related.extend(get_related_properties(property.iri)) for property in cap_input_properties]

		other_capabilities = [capability for capability in capabilities if capability.iri != cap.iri]
		other_capabilities_outputs: List[CapabilityPropertyInfluence] = []
		[other_capabilities_outputs.extend(other_cap.output_properties) for other_cap in other_capabilities]
		
		# For each cap input: Check if its part of another output
		for input in cap_input_and_related:
			output_in_inputs = next((output for output in other_capabilities_outputs if output.property.iri == input.iri), None)
			if output_in_inputs:
				capability_a_iri = next(iter(output_in_inputs.property.capability_iris))
				capability_b_iri = cap.iri
				# Check cap a is provided. Cap b is always as its from the array of provided caps
				cap_a_is_provided = next((cap for cap in capabilities if capability_a_iri == cap.iri), None)
				if not (cap_a_is_provided):
					continue

				# Filter out same caps
				if capability_a_iri == capability_b_iri:
					continue

				# Add to mutexes (duplicates are automatically handled as it's a set)
				capability_mutex_tuples.add(CapabilityTuple(capability_a_iri, capability_b_iri))

	# Hard-coded: Add Transport<>RawCylinderSupply
	capability_mutex_tuples.add(CapabilityTuple('http://www.hsu-hh.de/aut/ontologies/lab/MPS500/Transport#Transport', 'http://www.hsu-hh.de/aut/ontologies/lab/MPS500/RawCylinderSupplyModule#SupplyRawCylinder'))

	# Go over all tuples and create a mutex for every happening
	for cap_tuple in capability_mutex_tuples:
		for happening in range(happenings):
			cap_a = capability_dictionary.get_capability_occurrence(cap_tuple.capability_a, happening)
			cap_b = capability_dictionary.get_capability_occurrence(cap_tuple.capability_b, happening)
			constraint = Or(Not(cap_a.z3_variable), Not(cap_b.z3_variable))
			constraints.append(constraint)

	return constraints



class CapabilityTuple:
	def __init__(self, capability_a: str, capability_b: str):
		self.capability_a = capability_a
		self.capability_b = capability_b

	def __eq__(self, other):
		if isinstance(other, CapabilityTuple):
			return {self.capability_a, self.capability_b} == {other.capability_a, other.capability_b}
		return False

	def __hash__(self):
		# Use frozenset to create a hash independent of order
		return hash(frozenset([self.capability_a, self.capability_b]))