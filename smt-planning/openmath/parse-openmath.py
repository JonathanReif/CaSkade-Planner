from rdflib import Graph, Variable
from rdflib.term import Identifier
from rdflib.query import Result
from typing import Mapping, Callable, MutableSequence, List
from MathJsSymbolInformation import MathJsSymbolInformation
from OperatorDictionary import OperatorDictionary

APPLICATION = Variable("application")
ARG = Variable("arg")

def parseRdfInput(rdfString: str)-> Graph: 
	store = Graph()
	store.parse(rdfString)
	return store


def fromOpenMath(rdfString: str, rootApplicationIri: str) -> str:
	# Converts an OpenMath RDF representation into a textual, human-readable formula

	store = parseRdfInput(rdfString)
	
	# Query to get OpenMath applications with operators and variables. Works also for nested applications. Positions stores arguments position, 
	# so that, e.g.,  "x / y" and "y / x" can be distinguished. Protect this query at all cost...
	queryString = """
	PREFIX rdf: <http:#www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX OM: <http:#openmath.org/vocab/math#>

	SELECT ?application (count(?argumentList)-1 as ?position) ?operator ?argName ?argType ?arg WHERE {
		?application OM:arguments/rdf:rest* ?argumentList
			OM:operator ?operator.

		?argumentList rdf:rest*/rdf:first ?arg.
		?arg a ?argType.
		OPTIONAL {
			?arg OM:name ?argName.
		}
	}
	GROUP BY ?application ?argName ?operator ?argType ?arg
	"""
	
	# Fire query and get results as an array
	queryResults =  store.query(queryString)
	
	# Get root application to start the whole recursive parsing procedure
	rootApplication = getRootApplication(queryResults.bindings, rootApplicationIri)
	string = getArgumentsOfApplication(rootApplication, queryResults.bindings)
	
	return string


def createExpression(operator:MathJsSymbolInformation, argumentExpression: list[str] | str):
	# Creates a string expression for a given operator and arguments. Handles unary and binary functions 
	arity = operator.arity
	operatorSymbol = operator.symbol
	expression = ""
	if (arity == 1):
		# Unary operators are constructed like <operator>(argument), e.g., sin(x)
		expression = f"{operatorSymbol}({argumentExpression})"
	if (arity == 2):
		# Binary operators are constructed by concatenating operator and arguments, e.g. x + y + z...
		expression = operatorSymbol.join(argumentExpression)

	return expression


def getRootApplication(bindings: MutableSequence[Mapping[Variable, Identifier]], rootApplicationIri: str)-> Mapping[Variable, Identifier]:
	# Finds the root application element by searching for rootApplicationIri and making sure it is in fact a root application element.

	# Due to the query structure, finding the parent element is a bit tricky. To understand this def, it's best to execute the query separately and look at the results 
	# First, we filter for the given rootApplicationIri to look only for entries of the OpenMath expression we are interested in (this filters out other possible roots)
	# In addition, we check that these candidates are in fact root applications. Check that the value for ?application is no argument (?arg) to a "higher" parent application
	matchesRootApplicationIri: Callable[[Mapping[Variable, Identifier]], bool] = lambda binding: binding.get(APPLICATION) == rootApplicationIri
	hasNoHigherParent: Callable[[Mapping[Variable, Identifier]], bool] = lambda binding: not any(b.get(ARG) == binding.get(APPLICATION) for b in bindings)

	rootCandidates = list(filter(matchesRootApplicationIri and hasNoHigherParent, bindings))

	# We can then still have multiple rows within the bindings if the root application is a binary relation (e.g. for "y=x+z" and x=y).
	# If there are no sub applications, any line can be returend. If there is a sub application, this one must be returned
	ARGTYPE = Variable("argType")
	isApplication: Callable[[Mapping[Variable, Identifier]], bool] = lambda binding: binding.get(ARGTYPE) == "http:#openmath.org/vocab/math#Application"
	parentWithSubApplication = next(filter(isApplication, rootCandidates))

	if (parentWithSubApplication):
		# If there is a parent with a sub application, return this one
		rootApplication = parentWithSubApplication
	else: 
		# If not, simply return the first one. It doesn't matter as in later stages, all information will be retrieved
		rootApplication =  rootCandidates[0]
	
	# if (!rootApplication) throw new Error(`Error while finding root application with IRI ${rootApplicationIri}`)

	return rootApplication

def getArgumentsOfApplication(parentApplication: Mapping[Variable, Identifier], bindings: MutableSequence[Mapping[Variable, Identifier]])-> str:
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
		
		string = createExpression(operator, [*argumentNames, getArgumentsOfApplication(entry, bindings)])
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
		
		string = createExpression(operator, argumentNames)
	
	return string