#!/usr/bin/env python3
"""Test plugin API endpoints."""

import sys
import json
sys.path.insert(0, '/home/user/KosCMS')

from webcms.core.request import Request
from webcms.core.response import Response
from webcms.admin.admin_api import AdminAPI

# Create admin API instance
api = AdminAPI(db=None, auth=None)

# Test list_plugins
print("Testing list_plugins...")
request = Request({})
response = api.list_plugins(request)
print(f"Response status: {response.status_code}")
print(f"Response body: {response.body[:500] if hasattr(response, 'body') else 'N/A'}")

# Parse response
try:
    data = json.loads(response.body)
    plugins = data.get('plugins', [])
    print(f"\nFound {len(plugins)} plugins via API:")
    for p in plugins:
        print(f"  - {p.get('name')} v{p.get('version')}: active={p.get('active')}, installed={p.get('installed')}")
except Exception as e:
    print(f"Error parsing response: {e}")

# Test activation if we have plugins
if plugins:
    plugin_id = plugins[0].get('id') or plugins[0].get('name')
    print(f"\nTesting activate_plugin for '{plugin_id}'...")
    
    # First activate
    response = api.activate_plugin(request, plugin_id)
    print(f"Activate response: {response.status_code} - {response.body[:200]}")
    
    # Then deactivate
    response = api.deactivate_plugin(request, plugin_id)
    print(f"Deactivate response: {response.status_code} - {response.body[:200]}")

print("\nAPI test complete!")
