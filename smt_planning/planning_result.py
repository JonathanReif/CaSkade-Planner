
from typing import List, Dict
from z3 import ModelRef

from smt_planning.StateHandler import StateHandler
from smt_planning.dicts.PropertyDictionary import Property, PropertyDictionary
from smt_planning.dicts.CapabilityDictionary import Capability, CapabilityDictionary

class PropertyAppearance:
	def __init__(self, property: Property, value: int | str) -> None:
		self.property = property
		self.value = value


class CapabilityAppearance:
	def __init__(self, capability_iri: str):
		self.capability_iri = capability_iri
		self.inputs: List[PropertyAppearance] = []
		self.outputs: List[PropertyAppearance] = []

	def add_input(self, input: PropertyAppearance):
		self.inputs.append(input)
	
	def add_output(self, output: PropertyAppearance):
		self.outputs.append(output)

	def add_property_appearance(self, property_appearance: PropertyAppearance):
		if property_appearance.property.relation_type == "Input":
			self.add_input(property_appearance)
		if property_appearance.property.relation_type == "Output":
			self.add_output(property_appearance)


class PlanStep:
	def __init__(self,capability_appearances: List[CapabilityAppearance]):
		self.capability_appearances = capability_appearances
		self.duration = 0

	def add_capability_appearance(self, capability_appearance: CapabilityAppearance):
		self.capability_appearances.append(capability_appearance)


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
			plan_step = PlanStep([capability_appearance])
			self.plan_steps.insert(index, plan_step)

	def insert_step(self, index: int, capability_appearances: List[CapabilityAppearance]):
		plan_step = PlanStep(capability_appearances)
		self.plan_steps.insert(index, plan_step)
	
	def add_property_appearance(self, index: int, property_appearance: PropertyAppearance):
		property = property_appearance.property
		capability_iris = property.capability_iris
		
		for capability_iri in capability_iris:
			step = self.plan_steps[index]
			# Find the correct capability and add. Assumption: Every capability can only appear once per step - that should make sense
			capability_appearances = [capability_appearance for capability_appearance in step.capability_appearances if capability_appearance.capability_iri == capability_iri]
			if capability_appearances:
				capability_appearances[0].add_property_appearance(property_appearance)


class PlanningResult:
	def __init__(self, model: ModelRef, smt_problem_location: str, smt_result_location: str):
		self.plan = self.derive_plan_from_model(model)
		self.smt_problem_location = smt_problem_location
		self.smt_result_location = smt_result_location

	def derive_plan_from_model(self, model: ModelRef) -> Plan:
		property_dictionary = StateHandler().get_property_dictionary()
		capability_dictionary = StateHandler().get_capability_dictionary()

		# Loop over all the vars and sort everything out (try to find the corresponding property or capability):
		plan = Plan([])
		property_appearance_store: Dict[int, List[PropertyAppearance]] = {} 
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
				property_appearance = PropertyAppearance(property, variable_value )
				property_appearance_store.setdefault(happening, []).append(property_appearance)

		for property_appearance_item in property_appearance_store.items():
			happening = property_appearance_item[0]
			property_appearances = property_appearance_item[1]
			for property_appearance in property_appearances:
				plan.add_property_appearance(happening, property_appearance)

		return plan