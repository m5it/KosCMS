#!/usr/bin/env python3
"""Test plugin API directly without HTTP server."""

import sys
sys.path.insert(0, '/home/user/KosCMS')

from webcms.core.request import Request
from webcms.admin.admin_api import AdminAPI

# Create admin API instance (no db needed for plugins)
api = AdminAPI(db=None, auth=None)

# Test list_plugins
print("=" * 60)
print("Testing list_plugins...")
print("=" * 60)

request = Request({})
response = api.list_plugins(request)
print(f"Response: {response}")

import json
try:
    data = json.loads(response.body)
    plugins = data.get('plugins', [])
    print(f"\nFound {len(plugins)} plugins:")
    for p in plugins:
        print(f"  - ID: {p.get('id')}")
        print(f"    Name: {p.get('name')}")
        print(f"    Version: {p.get('version')}")
        print(f"    Description: {p.get('description', 'N/A')[:50]}...")
        print(f"    Active: {p.get('active')}")
        print(f"    Installed: {p.get('installed')}")
        print()
except Exception as e:
    print(f"Error parsing response: {e}")

# Test activation/deactivation if plugins exist
if plugins:
    plugin_id = plugins[0].get('id')
    
    print("=" * 60)
    print(f"Testing activate_plugin for '{plugin_id}'...")
    print("=" * 60)
    
    response = api.activate_plugin(request, plugin_id)
    print(f"Response: {response}")
    try:
        data = json.loads(response.body)
        print(f"Parsed: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Body: {response.body[:500] if hasattr(response, 'body') else response}")
    
    print()
    print("=" * 60)
    print(f"Testing deactivate_plugin for '{plugin_id}'...")
    print("=" * 60)
    
    response = api.deactivate_plugin(request, plugin_id)
    print(f"Response: {response}")
    try:
        data = json.loads(response.body)
        print(f"Parsed: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Body: {response.body[:500] if hasattr(response, 'body') else response}")

print("\n" + "=" * 60)
print("All tests complete!")
print("=" * 60)
