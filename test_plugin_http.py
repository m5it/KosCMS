#!/usr/bin/env python3
"""Test plugin API via HTTP."""

import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(url, method="GET", data=None):
    """Test an API endpoint."""
    full_url = f"{BASE_URL}{url}"
    try:
        if method == "GET":
            req = urllib.request.Request(full_url, method="GET")
        else:
            req = urllib.request.Request(
                full_url, 
                data=json.dumps(data).encode() if data else None,
                headers={'Content-Type': 'application/json'},
                method=method
            )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode())
    except Exception as e:
        return None, str(e)

# Test list plugins
print("Testing GET /api/v1/admin/plugins...")
status, data = test_endpoint("/api/v1/admin/plugins")
print(f"Status: {status}")
print(f"Response: {json.dumps(data, indent=2)[:500] if isinstance(data, dict) else data}")

if isinstance(data, dict) and 'plugins' in data and data['plugins']:
    plugin_id = data['plugins'][0].get('id')
    print(f"\nTesting POST /api/v1/admin/plugins/{plugin_id}/activate...")
    status, data = test_endpoint(f"/api/v1/admin/plugins/{plugin_id}/activate", method="POST")
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)[:300] if isinstance(data, dict) else data}")
    
    print(f"\nTesting POST /api/v1/admin/plugins/{plugin_id}/deactivate...")
    status, data = test_endpoint(f"/api/v1/admin/plugins/{plugin_id}/deactivate", method="POST")
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)[:300] if isinstance(data, dict) else data}")
else:
    print("\nNo plugins found to test activation/deactivation")

print("\nHTTP test complete!")
