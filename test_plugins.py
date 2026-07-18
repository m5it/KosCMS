#!/usr/bin/env python3
"""Test plugin discovery and registry."""

import sys
sys.path.insert(0, '/home/user/KosCMS')

from webcms.plugins.marketplace import get_registry

# Test registry
r = get_registry()
plugins = r.list_available()

print(f"Found {len(plugins)} plugins:")
for p in plugins:
    print(f"  - {p.name}: {p.version} (active={p.active}, installed={p.installed})")

# Test activation
if plugins:
    test_plugin = plugins[0].name
    print(f"\nTesting activation of '{test_plugin}':")
    success, msg = r.activate(test_plugin)
    print(f"  Activate: success={success}, msg={msg}")
    
    # Check state
    info = r.get_info(test_plugin)
    print(f"  State after activate: active={info.active}")
    
    # Test deactivation
    success, msg = r.deactivate(test_plugin)
    print(f"  Deactivate: success={success}, msg={msg}")
    
    info = r.get_info(test_plugin)
    print(f"  State after deactivate: active={info.active}")

print("\nPlugin registry test complete!")
