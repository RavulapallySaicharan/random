#!/usr/bin/env python3
"""
MLflow Trace Dumper

This script connects to an MLflow UI app and dumps all traces stored there.
It's specifically designed for LangGraph agent traces stored in MLflow.

Usage:
    python mlflow_trace_dumper.py --mlflow_url <your_mlflow_url> [options]

Example:
    python mlflow_trace_dumper.py --mlflow_url http://localhost:5000 --output traces_dump.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MLflowTraceDumper:
    """Class to handle dumping traces from MLflow UI app."""
    
    def __init__(self, mlflow_url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the MLflow trace dumper.
        
        Args:
            mlflow_url: URL of the MLflow UI app
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
    
    def get_all_experiments(self) -> List[Dict[str, Any]]:
        """
        Get all experiments from MLflow.
        
        Returns:
            List of experiment dictionaries
        """
        try:
            response = self.session.get(f"{self.mlflow_url}/api/2.0/mlflow/experiments/list")
            response.raise_for_status()
            experiments = response.json().get('experiments', [])
            logger.info(f"Found {len(experiments)} experiments")
            return experiments
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get experiments: {e}")
            return []
    
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
    
    def get_trace_data(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get trace data for a specific run.
        
        Args:
            run_id: ID of the run
            
        Returns:
            Trace data dictionary or None if not found
        """
        try:
            # Try to get trace data from MLflow
            response = self.session.get(f"{self.mlflow_url}/api/2.0/mlflow/runs/get", params={"run_id": run_id})
            response.raise_for_status()
            run_data = response.json().get('run', {})
            
            # Get run data including metrics, parameters, and tags
            trace_data = {
                "run_id": run_id,
                "run_data": run_data,
                "metrics": {},
                "parameters": {},
                "tags": {},
                "artifacts": []
            }
            
            # Get metrics
            metrics_response = self.session.get(
                f"{self.mlflow_url}/api/2.0/mlflow/metrics/get-history",
                params={"run_id": run_id}
            )
            if metrics_response.status_code == 200:
                trace_data["metrics"] = metrics_response.json().get('metrics', [])
            
            # Get parameters
            params_response = self.session.get(
                f"{self.mlflow_url}/api/2.0/mlflow/runs/get",
                params={"run_id": run_id}
            )
            if params_response.status_code == 200:
                run_info = params_response.json().get('run', {})
                trace_data["parameters"] = run_info.get('data', {}).get('params', {})
                trace_data["tags"] = run_info.get('data', {}).get('tags', {})
            
            # Try to get artifacts (including trace files)
            artifacts_response = self.session.get(
                f"{self.mlflow_url}/api/2.0/mlflow/artifacts/list",
                params={"run_id": run_id}
            )
            if artifacts_response.status_code == 200:
                artifacts = artifacts_response.json().get('files', [])
                trace_data["artifacts"] = artifacts
                
                # Try to download trace-specific artifacts
                for artifact in artifacts:
                    if any(keyword in artifact.get('path', '').lower() for keyword in ['trace', 'langraph', 'agent']):
                        try:
                            artifact_response = self.session.get(
                                f"{self.mlflow_url}/api/2.0/mlflow/artifacts/download",
                                params={
                                    "run_id": run_id,
                                    "path": artifact['path']
                                }
                            )
                            if artifact_response.status_code == 200:
                                trace_data[f"artifact_{artifact['path']}"] = artifact_response.text
                        except Exception as e:
                            logger.warning(f"Failed to download artifact {artifact['path']}: {e}")
            
            return trace_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get trace data for run {run_id}: {e}")
            return None
    
    def dump_all_traces(self, output_file: str = None) -> Dict[str, Any]:
        """
        Dump all traces from MLflow.
        
        Args:
            output_file: Optional file path to save the dump
            
        Returns:
            Dictionary containing all trace data
        """
        logger.info("Starting trace dump process...")
        
        all_traces = {
            "metadata": {
                "mlflow_url": self.mlflow_url,
                "dump_timestamp": datetime.now().isoformat(),
                "total_experiments": 0,
                "total_runs": 0,
                "total_traces": 0
            },
            "experiments": []
        }
        
        # Get all experiments
        experiments = self.get_all_experiments()
        all_traces["metadata"]["total_experiments"] = len(experiments)
        
        for experiment in experiments:
            experiment_id = experiment['experiment_id']
            experiment_name = experiment.get('name', 'Unknown')
            
            logger.info(f"Processing experiment: {experiment_name} (ID: {experiment_id})")
            
            experiment_data = {
                "experiment_info": experiment,
                "runs": []
            }
            
            # Get all runs for this experiment
            runs = self.get_runs_for_experiment(experiment_id)
            experiment_data["runs"] = runs
            all_traces["metadata"]["total_runs"] += len(runs)
            
            # Get trace data for each run
            for run in runs:
                run_id = run['info']['run_id']
                run_name = run['info'].get('run_name', 'Unknown')
                
                logger.info(f"  Processing run: {run_name} (ID: {run_id})")
                
                trace_data = self.get_trace_data(run_id)
                if trace_data:
                    run['trace_data'] = trace_data
                    all_traces["metadata"]["total_traces"] += 1
                else:
                    run['trace_data'] = None
            
            all_traces["experiments"].append(experiment_data)
        
        # Save to file if specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_traces, f, indent=2, ensure_ascii=False)
                logger.info(f"Trace dump saved to: {output_file}")
            except Exception as e:
                logger.error(f"Failed to save trace dump to file: {e}")
        
        logger.info(f"Trace dump completed. Found {all_traces['metadata']['total_traces']} traces across {all_traces['metadata']['total_runs']} runs in {all_traces['metadata']['total_experiments']} experiments.")
        
        return all_traces


def main():
    """Main function to run the MLflow trace dumper."""
    parser = argparse.ArgumentParser(description='Dump all traces from MLflow UI app')
    parser.add_argument('--mlflow_url', required=True, help='URL of the MLflow UI app')
    parser.add_argument('--username', help='Username for authentication (if required)')
    parser.add_argument('--password', help='Password for authentication (if required)')
    parser.add_argument('--output', default='mlflow_traces_dump.json', help='Output file path (default: mlflow_traces_dump.json)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create dumper instance
        dumper = MLflowTraceDumper(
            mlflow_url=args.mlflow_url,
            username=args.username,
            password=args.password
        )
        
        # Dump all traces
        traces = dumper.dump_all_traces(output_file=args.output)
        
        # Print summary
        print(f"\n=== Trace Dump Summary ===")
        print(f"MLflow URL: {traces['metadata']['mlflow_url']}")
        print(f"Dump timestamp: {traces['metadata']['dump_timestamp']}")
        print(f"Total experiments: {traces['metadata']['total_experiments']}")
        print(f"Total runs: {traces['metadata']['total_runs']}")
        print(f"Total traces found: {traces['metadata']['total_traces']}")
        print(f"Output file: {args.output}")
        
    except Exception as e:
        logger.error(f"Failed to dump traces: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 