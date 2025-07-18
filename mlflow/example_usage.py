#!/usr/bin/env python3
"""
Example usage of the MLflow Trace Dumper scripts

This script demonstrates how to use the trace dumper classes programmatically
instead of using the command-line interface.
"""

import json
from mlflow_trace_dumper import MLflowTraceDumper
from langraph_trace_dumper import LangGraphTraceDumper


def example_general_dumper():
    """Example of using the general MLflow trace dumper."""
    print("=== General MLflow Trace Dumper Example ===")
    
    # Initialize the dumper
    dumper = MLflowTraceDumper(
        mlflow_url="http://localhost:5000",
        # username="your_username",  # Uncomment if authentication is needed
        # password="your_password"   # Uncomment if authentication is needed
    )
    
    # Dump all traces
    traces = dumper.dump_all_traces(output_file="example_general_dump.json")
    
    # Print summary
    print(f"Found {traces['metadata']['total_traces']} traces")
    print(f"Across {traces['metadata']['total_runs']} runs")
    print(f"In {traces['metadata']['total_experiments']} experiments")
    
    return traces


def example_langraph_dumper():
    """Example of using the LangGraph-specific trace dumper."""
    print("\n=== LangGraph Trace Dumper Example ===")
    
    # Initialize the dumper
    dumper = LangGraphTraceDumper(
        mlflow_url="http://localhost:5000",
        # username="your_username",  # Uncomment if authentication is needed
        # password="your_password"   # Uncomment if authentication is needed
    )
    
    # Dump LangGraph traces
    traces = dumper.dump_langraph_traces(output_file="example_langraph_dump.json")
    
    # Print summary
    print(f"Found {traces['metadata']['total_langraph_traces']} LangGraph traces")
    print(f"Across {traces['metadata']['total_runs']} runs")
    print(f"In {traces['metadata']['total_experiments']} experiments")
    
    # Show details of found traces
    if traces['metadata']['total_langraph_traces'] > 0:
        print("\nLangGraph traces found:")
        for i, trace in enumerate(traces['langraph_traces'][:3]):  # Show first 3
            exp_name = trace.get('experiment_info', {}).get('name', 'Unknown')
            run_name = trace.get('run_info', {}).get('run_name', 'Unknown')
            trace_files = len(trace.get('trace_files', []))
            print(f"  {i+1}. {exp_name} > {run_name} ({trace_files} trace files)")
        
        if len(traces['langraph_traces']) > 3:
            print(f"  ... and {len(traces['langraph_traces']) - 3} more")
    
    return traces


def analyze_trace_content(traces):
    """Example of analyzing the trace content."""
    print("\n=== Trace Content Analysis ===")
    
    if not traces.get('langraph_traces'):
        print("No LangGraph traces found to analyze.")
        return
    
    # Analyze the first trace
    first_trace = traces['langraph_traces'][0]
    
    print(f"Analyzing trace: {first_trace.get('run_info', {}).get('run_name', 'Unknown')}")
    
    # Check for trace files
    trace_files = first_trace.get('trace_files', [])
    print(f"Number of trace files: {len(trace_files)}")
    
    for i, trace_file in enumerate(trace_files):
        print(f"\nTrace file {i+1}: {trace_file['path']}")
        print(f"  Size: {trace_file['size']} characters")
        
        # Try to parse and analyze the content
        content = trace_file['content']
        try:
            # Try to parse as JSON
            trace_data = json.loads(content)
            print(f"  Format: JSON")
            print(f"  Keys: {list(trace_data.keys()) if isinstance(trace_data, dict) else 'Not a dict'}")
            
            # Look for specific LangGraph structures
            if isinstance(trace_data, dict):
                if 'steps' in trace_data:
                    print(f"  Steps: {len(trace_data['steps'])}")
                if 'nodes' in trace_data:
                    print(f"  Nodes: {len(trace_data['nodes'])}")
                if 'edges' in trace_data:
                    print(f"  Edges: {len(trace_data['edges'])}")
                    
        except json.JSONDecodeError:
            print(f"  Format: Text (not JSON)")
            # Show first 200 characters
            preview = content[:200].replace('\n', ' ')
            print(f"  Preview: {preview}...")


def main():
    """Main function demonstrating usage."""
    print("MLflow Trace Dumper - Example Usage")
    print("=" * 50)
    
    try:
        # Example 1: General dumper
        general_traces = example_general_dumper()
        
        # Example 2: LangGraph dumper
        langraph_traces = example_langraph_dumper()
        
        # Example 3: Analyze trace content
        analyze_trace_content(langraph_traces)
        
        print("\n" + "=" * 50)
        print("Examples completed successfully!")
        print("Check the generated JSON files for the full trace data.")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure your MLflow server is running and accessible.")


if __name__ == "__main__":
    main() 