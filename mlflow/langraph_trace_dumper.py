#!/usr/bin/env python3
"""
LangGraph Trace Dumper for MLflow

This script is specifically designed to dump LangGraph agent traces from MLflow UI app.
It looks for LangGraph-specific trace data and artifacts.

Usage:
    python langraph_trace_dumper.py --mlflow_url <your_mlflow_url> [options]

Example:
    python langraph_trace_dumper.py --mlflow_url http://localhost:5000 --output langraph_traces.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LangGraphTraceDumper:
    """Specialized class for dumping LangGraph traces from MLflow."""
    
    def __init__(self, mlflow_url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the LangGraph trace dumper.
        
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
    
    def _is_langraph_trace(self, run_data: Dict[str, Any]) -> bool:
        """
        Check if a run contains LangGraph trace data.
        
        Args:
            run_data: Run data from MLflow
            
        Returns:
            True if it's a LangGraph trace, False otherwise
        """
        # Check tags for LangGraph indicators
        tags = run_data.get('data', {}).get('tags', {})
        for tag_key, tag_value in tags.items():
            if any(keyword in tag_key.lower() for keyword in ['langraph', 'agent', 'trace']):
                return True
            if any(keyword in str(tag_value).lower() for keyword in ['langraph', 'agent', 'trace']):
                return True
        
        # Check run name
        run_name = run_data.get('info', {}).get('run_name', '').lower()
        if any(keyword in run_name for keyword in ['langraph', 'agent', 'trace']):
            return True
        
        # Check experiment name
        experiment_name = run_data.get('info', {}).get('experiment_id', '').lower()
        if any(keyword in experiment_name for keyword in ['langraph', 'agent', 'trace']):
            return True
        
        return False
    
    def get_all_experiments(self) -> List[Dict[str, Any]]:
        """Get all experiments from MLflow."""
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
        """Get all runs for a specific experiment."""
        try:
            response = self.session.get(
                f"{self.mlflow_url}/api/2.0/mlflow/runs/search",
                params={
                    "experiment_ids": [experiment_id],
                    "max_results": 1000
                }
            )
            response.raise_for_status()
            runs = response.json().get('runs', [])
            logger.info(f"Found {len(runs)} runs for experiment {experiment_id}")
            return runs
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get runs for experiment {experiment_id}: {e}")
            return []
    
    def get_langraph_trace_data(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get LangGraph trace data for a specific run.
        
        Args:
            run_id: ID of the run
            
        Returns:
            LangGraph trace data dictionary or None if not found
        """
        try:
            # Get run data
            response = self.session.get(f"{self.mlflow_url}/api/2.0/mlflow/runs/get", params={"run_id": run_id})
            response.raise_for_status()
            run_data = response.json().get('run', {})
            
            # Check if this is a LangGraph trace
            if not self._is_langraph_trace(run_data):
                return None
            
            trace_data = {
                "run_id": run_id,
                "run_info": run_data.get('info', {}),
                "run_data": run_data.get('data', {}),
                "langraph_trace": {},
                "artifacts": [],
                "trace_files": []
            }
            
            # Get artifacts
            artifacts_response = self.session.get(
                f"{self.mlflow_url}/api/2.0/mlflow/artifacts/list",
                params={"run_id": run_id}
            )
            
            if artifacts_response.status_code == 200:
                artifacts = artifacts_response.json().get('files', [])
                trace_data["artifacts"] = artifacts
                
                # Look for LangGraph trace files
                for artifact in artifacts:
                    artifact_path = artifact.get('path', '')
                    
                    # Check for common LangGraph trace file patterns
                    if any(pattern in artifact_path.lower() for pattern in [
                        'trace.json', 'trace.jsonl', 'langraph_trace', 'agent_trace',
                        'trace_data', 'execution_trace', 'workflow_trace'
                    ]):
                        try:
                            # Download the trace file
                            artifact_response = self.session.get(
                                f"{self.mlflow_url}/api/2.0/mlflow/artifacts/download",
                                params={
                                    "run_id": run_id,
                                    "path": artifact_path
                                }
                            )
                            
                            if artifact_response.status_code == 200:
                                trace_content = artifact_response.text
                                trace_data["trace_files"].append({
                                    "path": artifact_path,
                                    "content": trace_content,
                                    "size": len(trace_content)
                                })
                                
                                # Try to parse as JSON
                                try:
                                    trace_json = json.loads(trace_content)
                                    trace_data["langraph_trace"][artifact_path] = trace_json
                                except json.JSONDecodeError:
                                    # If not JSON, store as text
                                    trace_data["langraph_trace"][artifact_path] = trace_content
                                    
                        except Exception as e:
                            logger.warning(f"Failed to download trace file {artifact_path}: {e}")
            
            # Extract LangGraph-specific information from tags and parameters
            tags = run_data.get('data', {}).get('tags', {})
            params = run_data.get('data', {}).get('params', {})
            
            langraph_info = {}
            for tag_key, tag_value in tags.items():
                if any(keyword in tag_key.lower() for keyword in ['langraph', 'agent', 'trace', 'workflow']):
                    langraph_info[f"tag_{tag_key}"] = tag_value
            
            for param_key, param_value in params.items():
                if any(keyword in param_key.lower() for keyword in ['langraph', 'agent', 'trace', 'workflow']):
                    langraph_info[f"param_{param_key}"] = param_value
            
            if langraph_info:
                trace_data["langraph_info"] = langraph_info
            
            return trace_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get LangGraph trace data for run {run_id}: {e}")
            return None
    
    def dump_langraph_traces(self, output_file: str = None) -> Dict[str, Any]:
        """
        Dump all LangGraph traces from MLflow.
        
        Args:
            output_file: Optional file path to save the dump
            
        Returns:
            Dictionary containing all LangGraph trace data
        """
        logger.info("Starting LangGraph trace dump process...")
        
        all_traces = {
            "metadata": {
                "mlflow_url": self.mlflow_url,
                "dump_timestamp": datetime.now().isoformat(),
                "total_experiments": 0,
                "total_runs": 0,
                "total_langraph_traces": 0
            },
            "langraph_traces": []
        }
        
        # Get all experiments
        experiments = self.get_all_experiments()
        all_traces["metadata"]["total_experiments"] = len(experiments)
        
        for experiment in experiments:
            experiment_id = experiment['experiment_id']
            experiment_name = experiment.get('name', 'Unknown')
            
            logger.info(f"Processing experiment: {experiment_name} (ID: {experiment_id})")
            
            # Get all runs for this experiment
            runs = self.get_runs_for_experiment(experiment_id)
            all_traces["metadata"]["total_runs"] += len(runs)
            
            # Get LangGraph trace data for each run
            for run in runs:
                run_id = run['info']['run_id']
                run_name = run['info'].get('run_name', 'Unknown')
                
                logger.info(f"  Processing run: {run_name} (ID: {run_id})")
                
                trace_data = self.get_langraph_trace_data(run_id)
                if trace_data:
                    trace_data["experiment_info"] = experiment
                    all_traces["langraph_traces"].append(trace_data)
                    all_traces["metadata"]["total_langraph_traces"] += 1
                    logger.info(f"    Found LangGraph trace data")
                else:
                    logger.debug(f"    No LangGraph trace data found")
        
        # Save to file if specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_traces, f, indent=2, ensure_ascii=False)
                logger.info(f"LangGraph trace dump saved to: {output_file}")
            except Exception as e:
                logger.error(f"Failed to save trace dump to file: {e}")
        
        logger.info(f"LangGraph trace dump completed. Found {all_traces['metadata']['total_langraph_traces']} LangGraph traces across {all_traces['metadata']['total_runs']} runs in {all_traces['metadata']['total_experiments']} experiments.")
        
        return all_traces


def main():
    """Main function to run the LangGraph trace dumper."""
    parser = argparse.ArgumentParser(description='Dump LangGraph traces from MLflow UI app')
    parser.add_argument('--mlflow_url', required=True, help='URL of the MLflow UI app')
    parser.add_argument('--username', help='Username for authentication (if required)')
    parser.add_argument('--password', help='Password for authentication (if required)')
    parser.add_argument('--output', default='langraph_traces_dump.json', help='Output file path (default: langraph_traces_dump.json)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create dumper instance
        dumper = LangGraphTraceDumper(
            mlflow_url=args.mlflow_url,
            username=args.username,
            password=args.password
        )
        
        # Dump all LangGraph traces
        traces = dumper.dump_langraph_traces(output_file=args.output)
        
        # Print summary
        print(f"\n=== LangGraph Trace Dump Summary ===")
        print(f"MLflow URL: {traces['metadata']['mlflow_url']}")
        print(f"Dump timestamp: {traces['metadata']['dump_timestamp']}")
        print(f"Total experiments: {traces['metadata']['total_experiments']}")
        print(f"Total runs: {traces['metadata']['total_runs']}")
        print(f"Total LangGraph traces found: {traces['metadata']['total_langraph_traces']}")
        print(f"Output file: {args.output}")
        
        if traces['metadata']['total_langraph_traces'] > 0:
            print(f"\nLangGraph traces found in experiments:")
            for trace in traces['langraph_traces']:
                exp_name = trace.get('experiment_info', {}).get('name', 'Unknown')
                run_name = trace.get('run_info', {}).get('run_name', 'Unknown')
                trace_files = len(trace.get('trace_files', []))
                print(f"  - {exp_name} > {run_name} ({trace_files} trace files)")
        
    except Exception as e:
        logger.error(f"Failed to dump LangGraph traces: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 