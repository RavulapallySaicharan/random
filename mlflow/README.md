# MLflow Trace Dumper

This repository contains Python scripts to dump all traces from an MLflow UI app, specifically designed for LangGraph agent traces.

## Scripts

### 1. `mlflow_trace_dumper.py` - General MLflow Trace Dumper
A comprehensive script that dumps all traces from MLflow, including metrics, parameters, tags, and artifacts.

### 2. `langraph_trace_dumper.py` - LangGraph-Specific Trace Dumper
A specialized script that focuses specifically on LangGraph agent traces, with better detection and parsing of LangGraph-specific data.

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### General MLflow Trace Dumper

```bash
python mlflow_trace_dumper.py --mlflow_url <your_mlflow_url> [options]
```

**Examples:**
```bash
# Basic usage
python mlflow_trace_dumper.py --mlflow_url http://localhost:5000

# With authentication
python mlflow_trace_dumper.py --mlflow_url http://localhost:5000 --username myuser --password mypass

# Custom output file
python mlflow_trace_dumper.py --mlflow_url http://localhost:5000 --output my_traces.json

# Verbose logging
python mlflow_trace_dumper.py --mlflow_url http://localhost:5000 --verbose
```

### LangGraph Trace Dumper

```bash
python langraph_trace_dumper.py --mlflow_url <your_mlflow_url> [options]
```

**Examples:**
```bash
# Basic usage
python langraph_trace_dumper.py --mlflow_url http://localhost:5000

# With authentication
python langraph_trace_dumper.py --mlflow_url http://localhost:5000 --username myuser --password mypass

# Custom output file
python langraph_trace_dumper.py --mlflow_url http://localhost:5000 --output langraph_traces.json

# Verbose logging
python langraph_trace_dumper.py --mlflow_url http://localhost:5000 --verbose
```

## Command Line Options

Both scripts support the following options:

- `--mlflow_url`: (Required) URL of your MLflow UI app
- `--username`: Username for authentication (if required)
- `--password`: Password for authentication (if required)
- `--output`: Output file path (default: `mlflow_traces_dump.json` or `langraph_traces_dump.json`)
- `--verbose` or `-v`: Enable verbose logging

## Output Format

The scripts generate JSON files with the following structure:

### General MLflow Dumper Output
```json
{
  "metadata": {
    "mlflow_url": "http://localhost:5000",
    "dump_timestamp": "2024-01-01T12:00:00",
    "total_experiments": 5,
    "total_runs": 25,
    "total_traces": 20
  },
  "experiments": [
    {
      "experiment_info": {...},
      "runs": [
        {
          "info": {...},
          "data": {...},
          "trace_data": {...}
        }
      ]
    }
  ]
}
```

### LangGraph Dumper Output
```json
{
  "metadata": {
    "mlflow_url": "http://localhost:5000",
    "dump_timestamp": "2024-01-01T12:00:00",
    "total_experiments": 5,
    "total_runs": 25,
    "total_langraph_traces": 15
  },
  "langraph_traces": [
    {
      "run_id": "...",
      "run_info": {...},
      "run_data": {...},
      "langraph_trace": {...},
      "artifacts": [...],
      "trace_files": [...],
      "langraph_info": {...},
      "experiment_info": {...}
    }
  ]
}
```

## Features

### General MLflow Dumper
- Dumps all experiments, runs, and their associated data
- Extracts metrics, parameters, tags, and artifacts
- Downloads trace-specific artifacts automatically
- Supports authentication
- Comprehensive logging

### LangGraph Dumper
- Specifically detects LangGraph traces using multiple heuristics
- Looks for LangGraph-specific keywords in tags, parameters, and names
- Downloads and parses trace files (JSON, JSONL, etc.)
- Extracts LangGraph-specific information
- More efficient for large MLflow instances with many non-LangGraph runs

## LangGraph Trace Detection

The LangGraph dumper uses several methods to identify LangGraph traces:

1. **Tag Analysis**: Looks for keywords like 'langraph', 'agent', 'trace', 'workflow' in tags
2. **Run Name Analysis**: Checks run names for LangGraph-related keywords
3. **Experiment Name Analysis**: Examines experiment names for relevant keywords
4. **Artifact Analysis**: Searches for trace files with patterns like:
   - `trace.json`
   - `trace.jsonl`
   - `langraph_trace`
   - `agent_trace`
   - `trace_data`
   - `execution_trace`
   - `workflow_trace`

## Error Handling

Both scripts include comprehensive error handling:
- Connection testing before starting
- Graceful handling of failed API calls
- Detailed logging of errors and warnings
- Continues processing even if individual runs fail

## Requirements

- Python 3.7+
- requests>=2.25.0
- mlflow>=2.0.0

## Troubleshooting

### Connection Issues
- Verify the MLflow URL is correct and accessible
- Check if authentication is required
- Ensure the MLflow server is running

### No Traces Found
- Check if your LangGraph traces are actually stored in MLflow
- Verify the trace detection keywords match your naming conventions
- Use the general dumper first to see all available data

### Large Output Files
- The scripts can generate large files for MLflow instances with many traces
- Consider using the LangGraph dumper for better filtering
- Use verbose logging to monitor progress

## License

This project is open source and available under the MIT License.

