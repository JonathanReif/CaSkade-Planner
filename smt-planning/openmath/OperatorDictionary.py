from MathJsSymbolInformation import MathJsSymbolInformation

class OperatorDictionary:
	mathJsToOpenMathMapping = {
		# Relations
		"=": "http://www.openmath.org/cd/relation1#eq",
		"<": "http://www.openmath.org/cd/relation1#lt", 
		">": "http://www.openmath.org/cd/relation1#gt", 
		"!=": "http://www.openmath.org/cd/relation1#neq",
		"<=": "http://www.openmath.org/cd/relation1#leq",
		">=": "http://www.openmath.org/cd/relation1#geq", 
		# Arithmetic operators
		"+": "http://www.openmath.org/cd/arith1#plus",
		"-": "http://www.openmath.org/cd/arith1#minus",
		"*": "http://www.openmath.org/cd/arith1#times",
		"/": "http://www.openmath.org/cd/arith1#divide",
		"sqrt": "http://www.openmath.org/cd/arith1#root",
		"pow": "http://www.openmath.org/cd/arith1#power",
		"abs": "http://www.openmath.org/cd/arith1#abs",
		# Transcendental functions
		"sin": "http://www.openmath.org/cd/transc1#sin",
		"cos": "http://www.openmath.org/cd/transc1#cos",
		"tan": "http://www.openmath.org/cd/transc1#tan",
	}

	openMathToMathJsMapping = {
		# Relations
		"http://www.openmath.org/cd/relation1#eq": MathJsSymbolInformation("=", 2),
		"http://www.openmath.org/cd/relation1#lt": MathJsSymbolInformation("<",2),
		"http://www.openmath.org/cd/relation1#gt": MathJsSymbolInformation(">",2),
		"http://www.openmath.org/cd/relation1#neq": MathJsSymbolInformation("!=", 2),
		"http://www.openmath.org/cd/relation1#leq": MathJsSymbolInformation("<=",2),
		"http://www.openmath.org/cd/relation1#geq": MathJsSymbolInformation(">=", 2),
		# Arithmetic operators
		"http://www.openmath.org/cd/arith1#plus": MathJsSymbolInformation("+", 2),
		"http://www.openmath.org/cd/arith1#minus": MathJsSymbolInformation("-", 2),
		"http://www.openmath.org/cd/arith1#times": MathJsSymbolInformation("*", 2),
		"http://www.openmath.org/cd/arith1#divide": MathJsSymbolInformation("/", 2),
		"http://www.openmath.org/cd/arith1#root": MathJsSymbolInformation("sqrt", 1),
		"http://www.openmath.org/cd/arith1#power": MathJsSymbolInformation("pow", 1),
		"http://www.openmath.org/cd/arith1#abs": MathJsSymbolInformation("abs", 1),
		# Transcendental functions
		"http://www.openmath.org/cd/transc1#sin": MathJsSymbolInformation("sin", 1),
		"http://www.openmath.org/cd/transc1#cos": MathJsSymbolInformation("cos", 1),
		"http://www.openmath.org/cd/transc1#tan": MathJsSymbolInformation("tan", 1),
	}

	@staticmethod
	def getOpenMathSymbol(mathJsSymbol: str) -> str:
		try:
			return OperatorDictionary.mathJsToOpenMathMapping[mathJsSymbol]
		except:
			return "http://www.openmath.org/cd/error#unhandled_symbol"

	@staticmethod
	def getMathJsSymbol(openMathSymbol: str)-> MathJsSymbolInformation:
		try:
			return OperatorDictionary.openMathToMathJsMapping[openMathSymbol]
		except:
			raise Exception(f"Error while finding the MathJS symbol for the OpenMath symbol {openMathSymbol}")