import os
from smt_planning.cask_to_smt import cask_to_smt
from smt_planning.planning_result import PlanningResult

class TestOneCap:
	
	def test_create_and_solve(self):
		ontology_file = os.getcwd() + "/ex_two_caps.ttl"
		max_happenings = 2
		expected_plan : PlanningResult = cask_to_smt(ontology_file, max_happenings, "./problem.smt", "plan.json") #type:ignore
		assert expected_plan.plan.plan_length == 2