from typing import List
from rdflib import Graph

from smt_planning.smt.StateHandler import StateHandler
from smt_planning.openmath.parse_openmath import from_open_math_in_graph

def getCapabilityConstraints(happenings: int, event_bound: int, query_handler) -> List[str]:
	# Get all capability constraint IRIs and check whether its a constraint on an input or output
	query_string = """
	PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX OM: <http://openmath.org/vocab/math#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
	SELECT ?cap ?constraint ?input ?inputArgument ?outputArgument WHERE {
		?constraint a OM:Application, CSS:CapabilityConstraint.
		?cap ^CSS:requiresCapability ?process;
			CSS:isRestrictedBy ?constraint.
		OPTIONAL {
			?constraint OM:arguments/rdf:rest*/rdf:first* ?inputArgument.
			?process VDI3682:hasInput/VDI3682:isCharacterizedBy ?inputArgument.
		}
		OPTIONAL {
			?constraint OM:arguments/rdf:rest*/rdf:first* ?outputArgument.
			?process VDI3682:hasOutput/VDI3682:isCharacterizedBy ?outputArgument.
		}
	}
	"""
	
	results = query_handler.query(query_string)
	input_constraints: List[ConstraintInfo] = []
	output_constraints: List[ConstraintInfo] = []
	for row in results:
		# As soon as an outputArgument is present, the constraint is considered an output constraint
		if row.outputArgument:																
			output_constraints.append(ConstraintInfo(str(row.cap), str(row.constraint)))	
		# If a row only has an inputArgument, the constraint is considered an input constraint
		if (row.inputArgument and not row.outputArgument):									 
			input_constraints.append(ConstraintInfo(str(row.cap), str(row.constraint)))		

	capability_dictionary = StateHandler().get_capability_dictionary()
	constraint_assertions = []
	for happening in range(happenings):
		for constraint_info in input_constraints:
			current_capability = capability_dictionary.get_capability_occurrence(constraint_info.cap, happening).z3_variable	
			infix_constraint = from_open_math_in_graph(query_handler, constraint_info.constraintIri, happening, 0)							
			prefix_expression = infix_to_prefix(infix_constraint)
			assertion = f"(assert (=> {(current_capability.sexpr())} ({prefix_expression})))"
			constraint_assertions.append(assertion)
		for constraint_info in output_constraints:
			current_capability = capability_dictionary.get_capability_occurrence(constraint_info.cap, happening).z3_variable	
			infix_constraint = from_open_math_in_graph(query_handler, constraint_info.constraintIri, happening, 1)							
			prefix_expression = infix_to_prefix(infix_constraint)
			assertion = f"(assert (=> {(current_capability.sexpr())} ({prefix_expression})))"
			constraint_assertions.append(assertion)

	return constraint_assertions



def infix_to_prefix(infix_expression):
	def precedence(operator):
		precedence_levels = {'=': 1, '+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
		return precedence_levels.get(operator, 0)

	def reverse_expression(expression):
		return ''.join(reversed(expression))

	def infix_to_postfix(expression):
		stack = []
		output = []
		expression = reverse_expression(expression)

		split_expression = expression.split(" ")

		for element in split_expression:
			if len(element) == 1: # Operator
				while stack and precedence(element) <= precedence(stack[-1]):
					output.append(stack.pop())
				element = add_space(element)
				stack.append(element)
			elif element == ')':
				element = add_space(element)
				stack.append(element)
			elif element == '(':
				while stack and stack[-1] != ')':
					output.append(stack.pop())
				stack.pop()  # Pop the '('
			else:  # Operand
				element = add_space(element)
				output.append(element)

		while stack:
			output.append(stack.pop())

		return reverse_expression(''.join(output))
	
	def add_space(element):
		padded_element = element + " "
		return padded_element

	return infix_to_postfix(infix_expression)



class ConstraintInfo():
	def __init__(self, cap: str, constraintIri: str):
		self.cap = cap
		self.constraintIri = constraintIri