from rdflib import Graph, Variable
from rdflib.term import Identifier
from rdflib.query import Result
from typing import Mapping, Callable, MutableSequence, List
from smt_planning.openmath.math_symbol_information import MathSymbolInformation
from smt_planning.openmath.operator_dictionary import OperatorDictionary

APPLICATION = Variable("application")
ARG = Variable("arg")

def from_open_math_in_graph( query_handler, rootApplicationIri: str, happening: int, event: int) -> str:
	# Converts OpenMath contained in a Graph into a textual, human-readable formula

	# Query to get OpenMath applications with operators and variables. Works also for nested applications. Positions stores arguments position, 
	# so that, e.g.,  "x / y" and "y / x" can be distinguished. Protect this query at all cost...
	# Note: We take the Data Element as ?argName instead of the actual arguments property OM:name. This is because we use DE IRIs as SMT variable names
	queryString = """
	PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX OM: <http://openmath.org/vocab/math#>
	PREFIX ont: <http://example.org/ontology#>
	PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
	
	SELECT ?application (count(?argumentList)-1 as ?position) ?operator ?argName ?argType ?arg WHERE {
		?application a OM:Application, CSS:CapabilityConstraint.
		?application OM:arguments/rdf:rest* ?argumentList;
			OM:operator ?operator.

		?argumentList rdf:rest*/rdf:first ?arg.
		?arg a ?argType.
		?argType rdfs:subClassOf OM:Object.
		OPTIONAL {
			#?arg OM:name ?argName.
			?argName DINEN61360:has_Instance_Description ?arg.
		}
	}
	GROUP BY ?application ?argName ?operator ?argType ?arg
	"""
	
	# Fire query and get results as an array
	queryResults = QueryCache.query(query_handler, queryString)
	
	# Get root application to start the whole recursive parsing procedure
	rootApplication = getRootApplication(queryResults.bindings, rootApplicationIri)
	string = getArgumentsOfApplication(rootApplication, queryResults.bindings, happening, event)
	
	return string


def createExpression(operator:MathSymbolInformation, argumentExpression: list[str] | str, happening: int, event: int):
	# Creates a string expression for a given operator and arguments. Handles unary and binary functions 
	arity = operator.arity
	operatorSymbol = f" {operator.symbol} "
	expression = ""
	if (arity == 1):
		# Unary operators are constructed like <operator>(argument), e.g., sin(x)
		expression = f"{operatorSymbol}({argumentExpression})"
	if (arity == 2):
		# Binary operators are constructed by concatenating operator and arguments, e.g. x + y + z...
		padded_expression = [f"|{elem}_{happening}_{event}|" for elem in argumentExpression]
		expression = operatorSymbol.join(padded_expression)

	return expression


def matches_Iri_and_has_no_higher_parent(bindings: MutableSequence[Mapping[Variable, Identifier]], rootApplicationIri: str):
	for binding in bindings:
		matchesRootApplicationIri = str(binding.get(APPLICATION)) == (rootApplicationIri)
		hasNoHigherParent = not any(b.get(ARG) == binding.get(APPLICATION) for b in bindings)
		if (matchesRootApplicationIri and hasNoHigherParent): 
			yield binding


def getRootApplication(bindings: MutableSequence[Mapping[Variable, Identifier]], rootApplicationIri: str)-> Mapping[Variable, Identifier]:
	# Finds the root application element by searching for rootApplicationIri and making sure it is in fact a root application element.

	# Due to the query structure, finding the parent element is a bit tricky. To understand this def, it's best to execute the query separately and look at the results 
	# First, we filter for the given rootApplicationIri to look only for entries of the OpenMath expression we are interested in (this filters out other possible roots)
	# In addition, we check that these candidates are in fact root applications. Check that the value for ?application is no argument (?arg) to a "higher" parent application
	# matchesRootApplicationIri: Callable[[Mapping[Variable, Identifier]], bool] = lambda binding: binding.get(APPLICATION) == rootApplicationIri
	# hasNoHigherParent: Callable[[Mapping[Variable, Identifier]], bool] = lambda binding: not any(b.get(ARG) == binding.get(APPLICATION) for b in bindings)
	rootCandidates = list(matches_Iri_and_has_no_higher_parent(bindings, rootApplicationIri))

	# We can then still have multiple rows within the bindings if the root application is a binary relation (e.g. for "y=x+z" and x=y).
	# If there are no sub applications, any line can be returend. If there is a sub application, this one must be returned
	ARGTYPE = Variable("argType")
	isApplication: Callable[[Mapping[Variable, Identifier]], bool] = lambda binding: str(binding.get(ARGTYPE)) == "http:#openmath.org/vocab/math#Application"
	parentWithSubApplication = list(filter(isApplication, rootCandidates))

	if (len(parentWithSubApplication) > 0):
		# If there is a parent with a sub application, return this one
		rootApplication = parentWithSubApplication[0]
	else: 
		# If not, simply return the first one. It doesn't matter as in later stages, all information will be retrieved
		rootApplication =  rootCandidates[0]
	
	# if (!rootApplication) throw new Error(`Error while finding root application with IRI ${rootApplicationIri}`)

	return rootApplication

def getArgumentsOfApplication(parentApplication: Mapping[Variable, Identifier], bindings: MutableSequence[Mapping[Variable, Identifier]], happening: int, event: int)-> str:
	# Check if there are more entries with arguments under the current element's application. This is the case for non-nested terms like x+y+z...
	filterSameApplications: Callable[[Mapping[Variable, Identifier]], bool] = lambda binding :binding.get(APPLICATION) == parentApplication.get(APPLICATION)
	argumentEntries = list(filter(filterSameApplications, bindings))
	
	# Check if the entry has children. If it has, we need to recursively go deeper

	hasChildren: Callable[[Mapping[Variable, Identifier]], bool] = lambda binding: binding.get(APPLICATION) == parentApplication.get(ARG)
	childApplications = list(filter(hasChildren, bindings))


	OPERATOR = Variable("operator")
	ARGNAME = Variable("argName")

	if (len(childApplications) > 0):
		entry = childApplications[0]
		openMathOperator = str(argumentEntries[0].get(OPERATOR))
		operator = OperatorDictionary.getMathJsSymbol(openMathOperator)

		argumentNames = list()
		for entry in argumentEntries:
			if entry.get(ARGNAME):
				argumentNames.append(str(entry.get(ARGNAME)))
		
		applicationArguments = getArgumentsOfApplication(entry, bindings, happening, event)
		string = createExpression(operator, [*argumentNames, applicationArguments], happening, event)
	else:
		allSameOperator = all(entry.get(OPERATOR) == argumentEntries[0].get(OPERATOR) for entry in argumentEntries)
		
		if (not allSameOperator):
			getOperatorNames = lambda binding: str(binding.get(OPERATOR))
			operators = list(map(getOperatorNames, argumentEntries))
			raise Exception(f"Error trying to obtain the operator of application. Multiple operators found: {str(operators)}")

		openMathOperator = str(argumentEntries[0].get(OPERATOR))
		operator = OperatorDictionary.getMathJsSymbol(openMathOperator)
		
		getArgNames: Callable[[Mapping[Variable, Identifier]], str] = lambda binding: str(binding.get(ARGNAME))
		argumentNames = list(map(getArgNames, argumentEntries))
		
		string = createExpression(operator, argumentNames, happening, event)
	
	return string




class QueryCache:
	query_result = None

	@staticmethod
	def query(query_handler, query_string: str):
		if(QueryCache.query_result is None):
			QueryCache.query_result = query_handler.query(query_string)		

		return QueryCache.query_result