#!/usr/bin/env python3
"""
Experiment Trace Dumper

This script dumps all traces from a specific MLflow experiment.
It's designed to work with the URL structure shown in the image.

Usage:
    python experiment_trace_dumper.py --mlflow_url <base_url> --experiment_id <experiment_id> [options]

Example:
    python experiment_trace_dumper.py --mlflow_url https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability --experiment_id 260533303499057285
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ExperimentTraceDumper:
    """Class to handle dumping traces from a specific MLflow experiment."""
    
    def __init__(self, mlflow_url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the experiment trace dumper.
        
        Args:
            mlflow_url: Base URL of the MLflow UI app
            username: Username for authentication (if required)
            password: Password for authentication (if required)
        """
        self.mlflow_url = mlflow_url.rstrip('/')
        self.session = requests.Session()
        
        # Set up authentication if provided
        if username and password:
            self.session.auth = (username, password)
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test the connection to MLflow server."""
        try:
            response = self.session.get(f"{self.mlflow_url}/health")
            if response.status_code == 200:
                logger.info("Successfully connected to MLflow server")
            else:
                logger.warning(f"MLflow server responded with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to MLflow server: {e}")
            raise
    
    def get_experiment_info(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific experiment.
        
        Args:
            experiment_id: ID of the experiment
            
        Returns:
            Experiment information dictionary or None if not found
        """
        try:
            response = self.session.get(f"{self.mlflow_url}/api/2.0/mlflow/experiments/get", params={"experiment_id": experiment_id})
            response.raise_for_status()
            experiment = response.json().get('experiment', {})
            logger.info(f"Found experiment: {experiment.get('name', 'Unknown')} (ID: {experiment_id})")
            return experiment
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get experiment {experiment_id}: {e}")
            return None
    
    def get_runs_for_experiment(self, experiment_id: str) -> List[Dict[str, Any]]:
        """
        Get all runs for a specific experiment.
        
        Args:
            experiment_id: ID of the experiment
            
        Returns:
            List of run dictionaries
        """
        try:
            response = self.session.get(
                f"{self.mlflow_url}/api/2.0/mlflow/runs/search",
                params={
                    "experiment_ids": [experiment_id],
                    "max_results": 1000  # Adjust as needed
                }
            )
            response.raise_for_status()
            runs = response.json().get('runs', [])
            logger.info(f"Found {len(runs)} runs for experiment {experiment_id}")
            return runs
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get runs for experiment {experiment_id}: {e}")
            return []
    
    def get_traces_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all traces for a specific run.
        
        Args:
            run_id: ID of the run
            
        Returns:
            List of trace dictionaries
        """
        traces = []
        
        try:
            # Method 1: Try to get traces using the traces API endpoint
            response = self.session.get(f"{self.mlflow_url}/api/2.0/mlflow/traces/search", params={"run_id": run_id})
            if response.status_code == 200:
                api_traces = response.json().get('traces', [])
                for trace in api_traces:
                    traces.append({
                        "trace_id": trace.get('trace_id', f"api_trace_{len(traces)}"),
                        "source": "api",
                        "data": trace,
                        "content": json.dumps(trace, indent=2)
                    })
                logger.info(f"Found {len(api_traces)} traces via API for run {run_id}")
            
            # Method 2: Try to get trace data from artifacts
            artifacts_response = self.session.get(
                f"{self.mlflow_url}/api/2.0/mlflow/artifacts/list",
                params={"run_id": run_id}
            )
            
            if artifacts_response.status_code == 200:
                artifacts = artifacts_response.json().get('files', [])
                
                for artifact in artifacts:
                    artifact_path = artifact.get('path', '')
                    
                    # Check for trace-related artifacts
                    if any(keyword in artifact_path.lower() for keyword in [
                        'trace', 'langraph', 'agent', 'execution', 'workflow', 'flow'
                    ]):
                        try:
                            artifact_response = self.session.get(
                                f"{self.mlflow_url}/api/2.0/mlflow/artifacts/download",
                                params={
                                    "run_id": run_id,
                                    "path": artifact_path
                                }
                            )
                            if artifact_response.status_code == 200:
                                trace_content = artifact_response.text
                                traces.append({
                                    "trace_id": artifact_path,
                                    "source": "artifact",
                                    "artifact_path": artifact_path,
                                    "content": trace_content,
                                    "size": len(trace_content)
                                })
                                logger.info(f"Downloaded trace artifact: {artifact_path}")
                        except Exception as e:
                            logger.warning(f"Failed to download trace artifact {artifact_path}: {e}")
            
            # Method 3: Try to get trace data from run tags and parameters
            run_response = self.session.get(f"{self.mlflow_url}/api/2.0/mlflow/runs/get", params={"run_id": run_id})
            if run_response.status_code == 200:
                run_data = run_response.json().get('run', {})
                tags = run_data.get('data', {}).get('tags', {})
                params = run_data.get('data', {}).get('params', {})
                
                # Look for trace-related tags and parameters
                trace_tags = {k: v for k, v in tags.items() if any(keyword in k.lower() for keyword in ['trace', 'langraph', 'agent'])}
                trace_params = {k: v for k, v in params.items() if any(keyword in k.lower() for keyword in ['trace', 'langraph', 'agent'])}
                
                if trace_tags or trace_params:
                    traces.append({
                        "trace_id": f"metadata_trace_{run_id}",
                        "source": "metadata",
                        "trace_tags": trace_tags,
                        "trace_params": trace_params,
                        "content": json.dumps({"tags": trace_tags, "params": trace_params}, indent=2)
                    })
                    logger.info(f"Found trace metadata for run {run_id}")
            
            logger.info(f"Total traces found for run {run_id}: {len(traces)}")
            return traces
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get traces for run {run_id}: {e}")
            return []
    
    def get_run_details(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific run.
        
        Args:
            run_id: ID of the run
            
        Returns:
            Run details dictionary or None if not found
        """
        try:
            response = self.session.get(f"{self.mlflow_url}/api/2.0/mlflow/runs/get", params={"run_id": run_id})
            response.raise_for_status()
            run_data = response.json().get('run', {})
            
            # Get metrics
            metrics_response = self.session.get(
                f"{self.mlflow_url}/api/2.0/mlflow/metrics/get-history",
                params={"run_id": run_id}
            )
            metrics = []
            if metrics_response.status_code == 200:
                metrics = metrics_response.json().get('metrics', [])
            
            # Get artifacts list
            artifacts_response = self.session.get(
                f"{self.mlflow_url}/api/2.0/mlflow/artifacts/list",
                params={"run_id": run_id}
            )
            artifacts = []
            if artifacts_response.status_code == 200:
                artifacts = artifacts_response.json().get('files', [])
            
            return {
                "run_data": run_data,
                "metrics": metrics,
                "artifacts": artifacts
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get run details for {run_id}: {e}")
            return None
    
    def dump_experiment_traces(self, experiment_id: str, output_file: str = None) -> Dict[str, Any]:
        """
        Dump all traces from a specific experiment.
        
        Args:
            experiment_id: ID of the experiment to dump
            output_file: Optional file path to save the dump
            
        Returns:
            Dictionary containing all trace data for the experiment
        """
        logger.info(f"Starting trace dump for experiment {experiment_id}...")
        
        # Get experiment information
        experiment_info = self.get_experiment_info(experiment_id)
        if not experiment_info:
            logger.error(f"Experiment {experiment_id} not found")
            return {}
        
        experiment_traces = {
            "metadata": {
                "mlflow_url": self.mlflow_url,
                "experiment_id": experiment_id,
                "experiment_name": experiment_info.get('name', 'Unknown'),
                "dump_timestamp": datetime.now().isoformat(),
                "total_runs": 0,
                "total_traces": 0
            },
            "experiment_info": experiment_info,
            "runs": []
        }
        
        # Get all runs for this experiment
        runs = self.get_runs_for_experiment(experiment_id)
        experiment_traces["metadata"]["total_runs"] = len(runs)
        
        for run in runs:
            run_id = run['info']['run_id']
            run_name = run['info'].get('run_name', 'Unknown')
            
            logger.info(f"Processing run: {run_name} (ID: {run_id})")
            
            # Get run details
            run_details = self.get_run_details(run_id)
            
            # Get traces for this run
            traces = self.get_traces_for_run(run_id)
            
            run_data = {
                "run_info": run,
                "run_details": run_details,
                "traces": traces
            }
            
            experiment_traces["metadata"]["total_traces"] += len(traces)
            experiment_traces["runs"].append(run_data)
            
            logger.info(f"  Found {len(traces)} traces for run {run_name}")
        
        # Save to file if specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(experiment_traces, f, indent=2, ensure_ascii=False)
                logger.info(f"Experiment trace dump saved to: {output_file}")
            except Exception as e:
                logger.error(f"Failed to save trace dump to file: {e}")
        
        logger.info(f"Experiment trace dump completed. Found {experiment_traces['metadata']['total_traces']} traces across {experiment_traces['metadata']['total_runs']} runs.")
        
        return experiment_traces


def main():
    """Main function to run the experiment trace dumper."""
    parser = argparse.ArgumentParser(description='Dump all traces from a specific MLflow experiment')
    parser.add_argument('--mlflow_url', required=True, help='Base URL of the MLflow UI app')
    parser.add_argument('--experiment_id', required=True, help='ID of the experiment to dump')
    parser.add_argument('--username', help='Username for authentication (if required)')
    parser.add_argument('--password', help='Password for authentication (if required)')
    parser.add_argument('--output', help='Output file path (default: experiment_<id>_traces.json)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set default output filename if not provided
    if not args.output:
        args.output = f"experiment_{args.experiment_id}_traces.json"
    
    try:
        # Create dumper instance
        dumper = ExperimentTraceDumper(
            mlflow_url=args.mlflow_url,
            username=args.username,
            password=args.password
        )
        
        # Dump experiment traces
        traces = dumper.dump_experiment_traces(args.experiment_id, output_file=args.output)
        
        # Print summary
        print(f"\n=== Experiment Trace Dump Summary ===")
        print(f"Experiment ID: {traces['metadata']['experiment_id']}")
        print(f"Experiment Name: {traces['metadata']['experiment_name']}")
        print(f"MLflow URL: {traces['metadata']['mlflow_url']}")
        print(f"Dump timestamp: {traces['metadata']['dump_timestamp']}")
        print(f"Total runs: {traces['metadata']['total_runs']}")
        print(f"Total traces found: {traces['metadata']['total_traces']}")
        print(f"Output file: {args.output}")
        
        # Show trace breakdown by run
        if traces['metadata']['total_traces'] > 0:
            print(f"\nTrace breakdown by run:")
            for run in traces['runs']:
                run_name = run['run_info']['info'].get('run_name', 'Unknown')
                run_id = run['run_info']['info']['run_id']
                trace_count = len(run['traces'])
                print(f"  - {run_name} ({run_id}): {trace_count} traces")
        
    except Exception as e:
        logger.error(f"Failed to dump experiment traces: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 