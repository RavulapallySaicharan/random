#!/usr/bin/env python3
"""
Example script to dump traces from the specific experiment shown in the image.

This script uses the experiment ID and base URL from the image to dump all traces.
"""

from experiment_trace_dumper import ExperimentTraceDumper
import json

def main():
    """Run the experiment trace dumper with the specific experiment ID."""
    
    # Configuration from the image
    MLFLOW_URL = "https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability"
    EXPERIMENT_ID = "260533303499057285"
    RUN_ID = "afbea05159bc478db519413af50395e2"  # From the image URL
    
    print("=== MLflow Experiment Trace Dumper ===")
    print(f"MLflow URL: {MLFLOW_URL}")
    print(f"Experiment ID: {EXPERIMENT_ID}")
    print(f"Run ID from URL: {RUN_ID}")
    print("=" * 50)
    
    try:
        # Create dumper instance
        dumper = ExperimentTraceDumper(mlflow_url=MLFLOW_URL)
        
        # Dump all traces from the experiment
        output_file = f"experiment_{EXPERIMENT_ID}_traces.json"
        traces = dumper.dump_experiment_traces(EXPERIMENT_ID, output_file=output_file)
        
        # Print detailed summary
        print(f"\n=== Trace Dump Results ===")
        print(f"Experiment Name: {traces['metadata']['experiment_name']}")
        print(f"Total Runs: {traces['metadata']['total_runs']}")
        print(f"Total Traces Found: {traces['metadata']['total_traces']}")
        print(f"Output File: {output_file}")
        
        # Show detailed breakdown
        if traces['metadata']['total_traces'] > 0:
            print(f"\n=== Detailed Trace Breakdown ===")
            for i, run in enumerate(traces['runs'], 1):
                run_name = run['run_info']['info'].get('run_name', 'Unknown')
                run_id = run['run_info']['info']['run_id']
                trace_count = len(run['traces'])
                
                print(f"\n{i}. Run: {run_name}")
                print(f"   Run ID: {run_id}")
                print(f"   Traces Found: {trace_count}")
                
                # Show trace details
                for j, trace in enumerate(run['traces'], 1):
                    trace_id = trace.get('trace_id', f'trace_{j}')
                    source = trace.get('source', 'unknown')
                    size = trace.get('size', 0)
                    
                    print(f"     {j}. Trace ID: {trace_id}")
                    print(f"        Source: {source}")
                    if size > 0:
                        print(f"        Size: {size} characters")
                    
                    # Show preview of trace content
                    content = trace.get('content', '')
                    if content:
                        preview = content[:100].replace('\n', ' ')
                        print(f"        Preview: {preview}...")
        
        # Check if the specific run from the URL was found
        specific_run_found = False
        for run in traces['runs']:
            if run['run_info']['info']['run_id'] == RUN_ID:
                specific_run_found = True
                print(f"\n=== Specific Run Analysis ===")
                print(f"Run from URL: {RUN_ID}")
                print(f"Run Name: {run['run_info']['info'].get('run_name', 'Unknown')}")
                print(f"Traces in this run: {len(run['traces'])}")
                break
        
        if not specific_run_found:
            print(f"\n⚠️  Warning: The specific run ID from the URL ({RUN_ID}) was not found in the experiment.")
        
        print(f"\n✅ Trace dump completed successfully!")
        print(f"📁 Check the file '{output_file}' for the complete trace data.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the MLflow server is accessible and the experiment ID is correct.")

if __name__ == "__main__":
    main() 