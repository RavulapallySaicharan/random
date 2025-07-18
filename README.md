# MLflow Trace Dumper

This repository contains Python scripts to dump all traces from an MLflow UI app, specifically designed for LangGraph agent traces.

## Quick Start for Your Use Case

Based on your MLflow URL, here's how to dump all traces from your specific experiment:

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Experiment Trace Dumper
```bash
python experiment_trace_dumper.py --mlflow_url https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability --experiment_id 260533303499057285
```

### 3. Or Use the Pre-configured Example
```bash
python run_example.py
```

This will dump all traces from experiment `260533303499057285` and save them to `experiment_260533303499057285_traces.json`.

## Scripts

### 1. `experiment_trace_dumper.py` - Specific Experiment Dumper (Recommended)
A specialized script that dumps all traces from a specific experiment ID. This is the best choice for your use case.

### 2. `mlflow_trace_dumper.py` - General MLflow Trace Dumper
A comprehensive script that dumps all traces from all experiments in MLflow.

### 3. `run_example.py` - Pre-configured Example
A ready-to-run example using your specific MLflow URL and experiment ID.

## Usage Examples

### For Your Specific Experiment
```bash
# Basic usage with your experiment
python experiment_trace_dumper.py --mlflow_url https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability --experiment_id 260533303499057285

# With custom output file
python experiment_trace_dumper.py --mlflow_url https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability --experiment_id 260533303499057285 --output my_traces.json

# With authentication (if required)
python experiment_trace_dumper.py --mlflow_url https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability --experiment_id 260533303499057285 --username myuser --password mypass

# Verbose logging
python experiment_trace_dumper.py --mlflow_url https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability --experiment_id 260533303499057285 --verbose
```

### General Usage
```bash
# Dump all experiments
python mlflow_trace_dumper.py --mlflow_url https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability

# Dump specific experiment using general dumper
python mlflow_trace_dumper.py --mlflow_url https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability --experiment_id 260533303499057285
```

## Command Line Options

### Experiment Trace Dumper
- `--mlflow_url`: (Required) Base URL of your MLflow UI app
- `--experiment_id`: (Required) ID of the experiment to dump
- `--username`: Username for authentication (if required)
- `--password`: Password for authentication (if required)
- `--output`: Output file path (default: `experiment_<id>_traces.json`)
- `--verbose` or `-v`: Enable verbose logging

### General MLflow Dumper
- `--mlflow_url`: (Required) URL of your MLflow UI app
- `--experiment_id`: Specific experiment ID to dump (optional)
- `--username`: Username for authentication (if required)
- `--password`: Password for authentication (if required)
- `--output`: Output file path (default: `mlflow_traces_dump.json`)
- `--verbose` or `-v`: Enable verbose logging

## Output Format

The scripts generate structured JSON files containing:

### Experiment Dumper Output
```json
{
  "metadata": {
    "mlflow_url": "https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability",
    "experiment_id": "260533303499057285",
    "experiment_name": "Your Experiment Name",
    "dump_timestamp": "2024-01-01T12:00:00",
    "total_runs": 5,
    "total_traces": 15
  },
  "experiment_info": {...},
  "runs": [
    {
      "run_info": {...},
      "run_details": {...},
      "traces": [
        {
          "trace_id": "trace_1",
          "source": "api|artifact|metadata",
          "content": "...",
          "size": 1024
        }
      ]
    }
  ]
}
```

## Trace Detection Methods

The scripts use multiple methods to find traces:

1. **API Traces**: Uses MLflow's traces API endpoint
2. **Artifact Traces**: Downloads trace files from artifacts
3. **Metadata Traces**: Extracts trace information from run tags and parameters

## Features

- **Comprehensive Trace Discovery**: Finds traces using multiple detection methods
- **Detailed Run Information**: Includes metrics, parameters, tags, and artifacts
- **Flexible Output**: Saves to JSON files with structured data
- **Error Handling**: Graceful handling of connection issues and missing data
- **Authentication Support**: Works with authenticated MLflow instances
- **Verbose Logging**: Detailed progress information

## Your Specific Setup

Based on your URL structure:
- **Base URL**: `https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability`
- **Experiment ID**: `260533303499057285`
- **Run ID**: `afbea05159bc478db519413af50395e2`

The scripts will:
1. Connect to your MLflow instance
2. Find all runs in experiment `260533303499057285`
3. Extract all traces from each run
4. Save everything to a structured JSON file

## Troubleshooting

### Connection Issues
- Verify the MLflow URL is accessible from your network
- Check if authentication is required
- Ensure the MLflow server is running

### No Traces Found
- Check if your LangGraph traces are actually stored in MLflow
- Verify the experiment ID is correct
- Use verbose logging to see what's being processed

### Authentication Issues
- If your MLflow instance requires authentication, use the `--username` and `--password` flags
- Check if you need to use a different authentication method (token, etc.)

## Requirements

- Python 3.7+
- requests>=2.25.0
- mlflow>=2.0.0

## License

This project is open source and available under the MIT License. 