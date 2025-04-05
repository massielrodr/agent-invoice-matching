# Agent for Amazon Invoice Matching
This project is designed to automate the process of matching invoice from Amazon with Internal Company Data. It leverages CrewAI for multi-agent task handling, Azure OpenAI for language model. The core functionality revolves around ensuring that invoice are being matching correctly.

### Features
- Extract text from PDFs using open-source libraries.
- Ensure that the model does not calculate values, but uses tools for this purpose.
- Optimize token consumption.

## Setup

1. Create Virtual Environment:
```bash
python -m venv .venv
```

2. Activate Virtual Environment (windows):
```bash
.venv\Scripts\Activate.ps1 
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Create a .env file and configure environment variables from the .env.example

## Usage

Run the script to execute the agents process:
```bash
python rebates_matching.py or events_matching.py
```

Run the script to execute the prompt chain example process:
```bash
python prompt_example.py
```

The script will:
- List PDFs files from the path docs/rebates/
- For each file the Agentic AI will do the Invoice Matching.
- Generate a list of json files with the information for it matching.

### Disabling Telemetry
The script includes a helper function disable_crewai_telemetry() to disable telemetry logging from CrewAI.