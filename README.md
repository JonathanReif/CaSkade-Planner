<img align="left" height="100px" src="https://avatars.githubusercontent.com/u/149593817?s=200&v=4">
<h1>CaSkade Planner - Capability-based Process Planning using SMT</h1>

CaSkade-Planner is an automated planning approach to derive process sequences that consist of provided capabilities for one or more required capabilities. It makes use of the [CaSk ontology](https://github.com/CaSkade-Automation/CaSk).

## Installation
Make sure that you have [Poetry](https://python-poetry.org/) installed. Clone this repository and install everything using `poetry install`. Afterwards you can use CaSkade-Planner according to the instructions below.

## How to use
### CLI
CaSkade-Planner provides a command-line interface with two main commands. You can always open the help with the `--help` option.

#### Plan from local ontology file
To plan from a local ontology file, use: `poetry run caskade-planner-cli plan-from-file`

```
Arguments:
  ONTOLOGY_FILE           Path to your ontology that is used for generating the
                          planning problem  [required]
  REQUIRED_CAPABILITY_IRI IRI of the required capability to plan for  [required]

Options:
  -mh, --max-happenings INTEGER  Maximum number of happenings to consider
                                 [default: 20]
  -problem, --problem-file TEXT  Path to where the generated problem will be
                                 stored
  -model, --model-file TEXT      Path to where the model file will be stored
                                 after solving
  -plan, --plan-file TEXT        Path to where the plan file will be stored
                                 after solving and transformation
  --help                         Show this message and exit.
```

**Example:**
```bash
poetry run caskade-planner-cli plan-from-file my-ontology.ttl http://example.org/capabilities#RequiredCapability1
```

#### Plan from SPARQL endpoint
To plan directly from a SPARQL endpoint, use: `poetry run caskade-planner-cli plan-from-endpoint`

```
Arguments:
  ENDPOINT_URL            URL of the SPARQL endpoint  [required]
  REQUIRED_CAPABILITY_IRI IRI of the required capability to plan for  [required]

Options:
  -mh, --max-happenings INTEGER  Maximum number of happenings to consider
                                 [default: 20]
  -problem, --problem-file TEXT  Path to where the generated problem will be
                                 stored
  -model, --model-file TEXT      Path to where the model file will be stored
                                 after solving
  -plan, --plan-file TEXT        Path to where the plan file will be stored
                                 after solving and transformation
  --help                         Show this message and exit.
```

**Example:**
```bash
poetry run caskade-planner-cli plan-from-endpoint localhost:7200/repositories/test-repo http://example.org/capabilities#RequiredCapability1
```

The `plan-from-endpoint` command outputs the result as JSON to stdout, making it easy to integrate with other tools.

### REST-API
If you want to use CaSkade-Planner as a standalone planning service to be used by other software components, you can integrate it as a REST API.
After cloning and installing the project, start the REST API by calling `poetry run caskade-planner-api`. The planning API runs on port 5000.

#### Endpoints

- `GET /ping` - Health check endpoint (returns 204 No Content)
- `POST /plan` - Main planning endpoint

#### Planning Request
Send an HTTP POST request to `<API-Address>:5000/plan` with a JSON body:

```json
{
  "mode": "file" | "sparql-endpoint",
  "requiredCapabilityIri": "<IRI of the required capability>",
  "maxHappenings": 5,  // optional, defaults to 5
  "endpointUrl": "<SPARQL endpoint URL>"  // only for mode="sparql-endpoint"
}
```

For `mode="file"`, you need to upload the ontology file as multipart/form-data with the key `"ontology-file"`.

#### Response Format
Both CLI and REST API return results in JSON format:

```json
{
  "timeCreated": "2024-01-01T12:00:00Z",
  "resultType": "sat" | "unsat",
  "plan": {  // only if resultType="sat"
    "plan_steps": [...],
    "plan_length": 5,
    "total_duration": 120
  },
  "unsatCore": [...]  // only if resultType="unsat"
}
```

### PyPI package
🚧 Coming soon 🚧
