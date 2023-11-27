import os
import tempfile
from flask import Flask
from flask import request, flash, redirect
from werkzeug.utils import secure_filename
from flask_cors import CORS

from smt_planning.smt.cask_to_smt import CaskadePlanner

UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'txt', 'ttl', 'xml', 'owl', 'json'}

# Create API 
app = Flask(__name__)
cors = CORS(app)
app.secret_key = 'the random string'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
	return '.' in filename and \
			filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def setup_planner_with_file(files):
	if 'ontology-file' not in files:
		flash('No file part')
		return redirect(request.url)
	
	file = files['ontology-file']
	# If the user does not select a file, the browser submits an
	# empty file without a filename.
	if file.filename == '':
		flash('No selected file')
		return redirect(request.url)
	if file and allowed_file(file.filename):
		filename = secure_filename(file.filename)
		filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
		file.save(filename)

		planner = CaskadePlanner()
		planner.with_file_query_handler(filename)
		return planner

@app.route('/') # type: ignore
def hello():
    return "Welcome to CaSkade Planner!"

# Wait for POST requests with a query param ?mode to /plan
@app.post('/plan') # type: ignore
def generate_and_solve_plan():
	mode = request.args.get('mode')
	planner: CaskadePlanner
	
	if mode == 'file':
		try:
			planner = setup_planner_with_file(request.files) # type: ignore
		except:
			print("Error during file upload")
		
	if mode == 'sparql-endpoint':
		endpoint_url = request.args.get('endpoint-url')
		planner = CaskadePlanner()
		planner.with_endpoint_query_handler(endpoint_url)

	max_happenings = request.args.get('max-happenings',type=int)
	result = planner.cask_to_smt(max_happenings)
	
	return result.as_dict()

def run():
	app.run()

if __name__ == '__main__': 
	run()