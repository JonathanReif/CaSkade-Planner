import os
import tempfile
from flask import Flask
from flask import request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from flask_cors import CORS
import zlib

from smt_planning.smt.cask_to_smt import cask_to_smt

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


# Wait for POST requests with a query param ?mode to /plan
@app.post('/plan') # type: ignore
def generate_and_solve_plan():
	mode = request.args.get('mode')
	if mode == 'file':
	
		if 'ontology-file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['ontology-file']
		# If the user does not select a file, the browser submits an
		# empty file without a filename.
		if file.filename == '':
			flash('No selected file')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
			file.save(filename)
		
			max_happenings = 10
			
			result = cask_to_smt(filename, max_happenings)
			os.remove(filename)
	
	if mode == 'sparql-endpoint':
		endpoint_url = request.args.get('endpoint_url')
		result = {}
		result["url"] = endpoint_url

	return result.as_dict()


if __name__ == '__main__': 
	app.run()