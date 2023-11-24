
import json
from datetime import datetime
from typing import List, Dict, Set
from z3 import ModelRef, RatNumRef, IntNumRef, BoolRef

from smt_planning.smt.StateHandler import StateHandler
from smt_planning.dicts.PropertyDictionary import Property

class PropertyAppearance:
	def __init__(self, property: Property, event: int, value: RatNumRef | BoolRef | IntNumRef) -> None:
		self.property = property
		self.event = event
		# Value has to be cast manually using z3's functions
		if type(value).__name__ == 'RatNumRef':
			self.value = float(value.as_decimal(20))
		elif type(value).__name__ == 'BoolRef':
			self.value = value.__bool__()
		elif type(value).__name__ == 'IntNumRef':
			self.value = int(str(value))
		else:
			raise NameError(f"No cast operation for type {type(value).__name__} of variabel {value} defined")

	def as_dict(self) -> Dict[str, object]:
		val = self.value
		dict = {
			"property_iri": self.property.iri,
			"value": self.value
		}
		return dict
	
	def __eq__(self, other):
		if isinstance(other, PropertyAppearance):
			return ((self.property.iri == other.property.iri))
		else:
			return False
		
	def __hash__(self):
		return hash(self.property.iri)


class CapabilityAppearance:
	def __init__(self, capability_iri: str):
		self.capability_iri = capability_iri
		self.inputs: Set[PropertyAppearance] = set()
		self.outputs: Set[PropertyAppearance] = set()

	def add_input(self, input: PropertyAppearance):
		if input.event != 0:
			return
		self.inputs.add(input)
	
	def add_output(self, output: PropertyAppearance):
		if output.event != 1:
			return
		self.outputs.add(output)

	def add_property_appearance(self, property_appearance: PropertyAppearance):
		if property_appearance.property.relation_type == "Input":
			self.add_input(property_appearance)
		if property_appearance.property.relation_type == "Output":
			self.add_output(property_appearance)
		
	def as_dict(self) -> Dict[str, object]:
		dict = {
			"capability_iri": self.capability_iri,
			"inputs": [input.as_dict() for input in self.inputs],
			"outputs": [output.as_dict() for output in self.outputs]
		}
		return dict


class PlanStep:
	def __init__(self, capability_appearances: List[CapabilityAppearance], index: int):
		self.capability_appearances = capability_appearances
		self.step_number= index
		self.duration = 0

	def add_capability_appearance(self, capability_appearance: CapabilityAppearance):
		self.capability_appearances.append(capability_appearance)

	def as_dict(self) -> Dict[str, object]:
		dict = {
			"duration": self.duration,
			"step_number": self.step_number,
			"capability_applications": [capability_appearance.as_dict() for capability_appearance in self.capability_appearances]
		}
		return dict


class Plan:
	def __init__(self, plan_steps: List[PlanStep]):
		self.plan_steps = plan_steps
		self.plan_length = len(plan_steps)
		step_durations = [step.duration for step in plan_steps]
		self.total_duration = sum(step_durations)
	
	def insert_capability_appearance(self, index: int, capability_appearance: CapabilityAppearance):
		if index in self.plan_steps:
			self.plan_steps[index].add_capability_appearance(capability_appearance)
		else:
			plan_step = PlanStep([capability_appearance], index)
			self.plan_steps.insert(index, plan_step)

	def insert_step(self, index: int, capability_appearances: List[CapabilityAppearance]):
		plan_step = PlanStep(capability_appearances, index)
		self.plan_steps.insert(index, plan_step)
		# Update plan length
		self.plan_length = len(self.plan_steps)
	
	def add_property_appearance(self, index: int, property_appearance: PropertyAppearance):
		property = property_appearance.property
		capability_iris = property.capability_iris
		
		for capability_iri in capability_iris:
			step = self.plan_steps[index]
			# Find the correct capability and add. Assumption: Every capability can only appear once per step - that should make sense
			capability_appearances = [capability_appearance for capability_appearance in step.capability_appearances if capability_appearance.capability_iri == capability_iri]
			if capability_appearances:
				capability_appearances[0].add_property_appearance(property_appearance)

		# Update plan length
		self.plan_length = len(self.plan_steps)
	
	def as_dict(self) -> Dict[str, object]:
		dict = {
			"plan_steps": [plan_step.as_dict() for plan_step in self.plan_steps],
			"plan_length":  self.plan_length,
			"total_duration": self.total_duration
		}
		return dict


class PlanningResult:
	def __init__(self, model: ModelRef):
		self.time_created = datetime.now()
		self.plan = self.derive_plan_from_model(model)

	def derive_plan_from_model(self, model: ModelRef) -> Plan:
		property_dictionary = StateHandler().get_property_dictionary()
		capability_dictionary = StateHandler().get_capability_dictionary()

		# Loop over all the vars and sort everything out (try to find the corresponding property or capability):
		plan = Plan([])
		property_appearance_store: Dict[int, List[PropertyAppearance]] = {} 	# store is a dict with happenings as a key
		for variable in model:
			variable_value = model[variable]
			# Filter out these pesty comments
			if (str(variable).startswith("##") and str(variable).endswith("##")):
				continue
				
			try:
				capability = capability_dictionary.get_capability_from_z3_variable(variable) # type: ignore
				if(variable_value == True):
					capability_appearance = CapabilityAppearance(capability.iri)
					plan.insert_capability_appearance(capability.happening, capability_appearance)
			except:
				property_occurrence = property_dictionary.get_property_from_z3_variable(variable) # type: ignore
				property = property_dictionary.get_property(property_occurrence.iri)
				happening = property_occurrence.happening
				event = property_occurrence.event
				property_occurrence.iri
				property_appearance = PropertyAppearance(property, event, variable_value)
				property_appearance_store.setdefault(happening, []).append(property_appearance)

		for property_appearance_item in property_appearance_store.items():
			happening = property_appearance_item[0]
			property_appearances = property_appearance_item[1]
			for property_appearance in property_appearances:
				plan.add_property_appearance(happening, property_appearance)

		return plan
	
	def as_dict(self) -> Dict[str, object]:
		dict = {
			"time-created": str(self.time_created),
			"plan": self.plan.as_dict()
		}
		return dict