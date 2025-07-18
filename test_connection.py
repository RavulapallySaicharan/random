#!/usr/bin/env python3
"""
Test connection to MLflow server to find the correct API endpoints.
"""

import requests
import sys
from urllib.parse import urljoin

def test_url_patterns(base_url):
    """Test different URL patterns to find the correct MLflow API endpoint."""
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    # Different possible API base URLs
    test_urls = [
        f"{base_url}/api/2.0/mlflow/experiments/list",
        f"{base_url}/api/2.0/mlflow/experiments/list",
        f"{base_url}/mlflow/api/2.0/mlflow/experiments/list",
        f"{base_url}/api/2.0/mlflow/experiments/list",
        f"{base_url}/experiments/list",
        f"{base_url}/mlflow/experiments/list",
    ]
    
    print(f"Testing connection to: {base_url}")
    print("=" * 60)
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"\n{i}. Testing: {test_url}")
        try:
            response = requests.get(test_url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS! Found working API endpoint")
                data = response.json()
                if 'experiments' in data:
                    print(f"   Found {len(data['experiments'])} experiments")
                    return test_url.replace('/experiments/list', '')
                else:
                    print(f"   Response: {data}")
            elif response.status_code == 401:
                print(f"   🔐 Requires authentication")
            elif response.status_code == 403:
                print(f"   🚫 Forbidden - may need authentication")
            elif response.status_code == 404:
                print(f"   ❌ Not found")
            else:
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed")
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None

def test_health_endpoints(base_url):
    """Test different health endpoint patterns."""
    
    base_url = base_url.rstrip('/')
    
    health_urls = [
        f"{base_url}/health",
        f"{base_url}/api/2.0/mlflow/health",
        f"{base_url}/mlflow/health",
        f"{base_url}/ping",
        f"{base_url}/api/ping",
    ]
    
    print(f"\nTesting health endpoints:")
    print("=" * 40)
    
    for i, health_url in enumerate(health_urls, 1):
        print(f"\n{i}. Testing: {health_url}")
        try:
            response = requests.get(health_url, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Health endpoint found!")
                return health_url
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None

def main():
    """Main function to test MLflow connection."""
    
    # Your MLflow URL from the image
    mlflow_url = "https://ssds-dev-ingress.statestr.com/ssds/dev/rcd/01/snoaiobservability"
    
    print("MLflow Connection Tester")
    print("=" * 60)
    
    # Test API endpoints
    api_base = test_url_patterns(mlflow_url)
    
    # Test health endpoints
    health_endpoint = test_health_endpoints(mlflow_url)
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    
    if api_base:
        print(f"✅ Working API base URL: {api_base}")
        print(f"\nTry using this URL with the dumper:")
        print(f"python experiment_trace_dumper.py --mlflow_url {api_base} --experiment_id 260533303499057285")
    else:
        print("❌ No working API endpoint found")
        print("\nPossible issues:")
        print("1. Authentication required")
        print("2. Different URL structure")
        print("3. Network connectivity issues")
        print("4. MLflow server not running")
    
    if health_endpoint:
        print(f"✅ Health endpoint: {health_endpoint}")
    else:
        print("❌ No health endpoint found")

if __name__ == "__main__":
    main() 