from typing import List

from smt_planning.smt.StateHandler import StateHandler

def get_capability_constraints():
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
	
	stateHandler = StateHandler()
	capability_dictionary = stateHandler.get_capability_dictionary()
	query_handler = stateHandler.get_query_handler()
	results = query_handler.query(query_string)
	
	for row in results:
		# As soon as an outputArgument is present, the constraint is considered an output constraint
		if row['outputArgument']:																
			capability_dictionary.add_capability_constraint(str(row['cap']), str(row['constraint']))
		# If a row only has an inputArgument, the constraint is considered an input constraint
		if (row['inputArgument'] and not row['outputArgument']):									 
			capability_dictionary.add_capability_constraint(str(row['cap']), str(row['constraint']), True)