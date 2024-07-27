import os

from smt_planning.openmath.parse_openmath import from_open_math_in_graph
from smt_planning.ontology_handling.query_handlers import FileQueryHandler

class TestThreeCaps:
	
	def test_create_and_solve(self):
		# Relativer Pfad
		ontology_file = os.path.join(os.getcwd(), "tests", "openmath-tests", "cylinder-supply.ttl")
		# ontology_file = os.path.join(os.getcwd(), "tests", "riva_one_rover.ttl")

		# Absoluter Pfad
		absolute_ontology_file = os.path.abspath(ontology_file)

		# Convert to file URI
		file_uri = absolute_ontology_file.replace("\\", "/")
		query_handler = FileQueryHandler(file_uri)
		equation = from_open_math_in_graph(query_handler, "http://www.hsu-hh.de/aut/ontologies/lab/MPS500/RawCylinderSupplyModule#ColorStackConstraint", 1, 1)
		expected_equation = ":ProductStack1CurrentColor_ID = :RawCylinderColor_ID or :ProductStack2CurrentColor_ID = :RawCylinderColor_ID or :ProductStack3CurrentColor_ID = :RawCylinderColor_ID"
		print(equation)
		assert(equation == expected_equation)


t = TestThreeCaps()
t.test_create_and_solve()