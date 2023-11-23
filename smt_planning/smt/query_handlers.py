from rdflib import Graph
import json
import requests
from smt_planning.smt.StateHandler import StateHandler

class FileQueryHandler:
	def __init__(self, filename) -> None:
		# Create a Graph
		state_handler = StateHandler()
		graph = Graph()
		state_handler.set_graph(graph)

		# Parse in an RDF file hosted beside this file
		graph.parse(filename, format="turtle")
	
	def query(self, query_string: str):
		graph = StateHandler().get_graph()
		results = graph.query(query_string)
		return results
	


class SparqlEndpointQueryHandler:
	def __init__(self, endpoint_url) -> None:
		self.endpoint_url = endpoint_url
		# Define the headers
		self.headers = {
			"Accept": "application/sparql-results+json",  # or "application/sparql-results+xml" for XML format
			"Content-Type": "application/sparql-query"
		}
	

	def query(self, query_string: str):

		# Send the request
		response = requests.post(self.endpoint_url, data=query_string, headers=self.headers)

		# Check if the request was successful
		if response.status_code == 200:
			# Process the results
			print("Query successful. Here are the results:")
			print(response.text)
			response_object = json.loads(response.text)
			return response_object.get('results').get('bindings')
		else:
			print("Query failed. Status code:", response.status_code)
			return
