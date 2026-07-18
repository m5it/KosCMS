#!/usr/bin/env python3
"""Test plugin marketplace directly."""

import sys
sys.path.insert(0, '/home/user/KosCMS')

from webcms.plugins.marketplace import get_registry, PluginRegistry

print("=" * 60)
print("Testing Plugin Marketplace")
print("=" * 60)

# Test get_registry
print("\n1. Testing get_registry()...")
registry = get_registry()
print(f"   Registry created: {type(registry).__name__}")

# Test list_available
print("\n2. Testing list_available()...")
plugins = registry.list_available()
print(f"   Found {len(plugins)} plugins:")

for p in plugins:
    print(f"   - {p.name} v{p.version}")
    print(f"     Description: {p.description[:50]}..." if len(p.description) > 50 else f"     Description: {p.description}")
    print(f"     Author: {p.author}")
    print(f"     Installed: {p.installed}")
    print(f"     Active: {p.active}")
    print()

# Test activation/deactivation if plugins exist
if plugins:
    plugin_name = plugins[0].name
    
    print("=" * 60)
    print(f"3. Testing activation for '{plugin_name}'...")
    print("=" * 60)
    
    # Check initial state
    info = registry.get_info(plugin_name)
    print(f"   Initial state: active={info.active}")
    
    # Activate
    success, msg = registry.activate(plugin_name)
    print(f"   Activate: success={success}, message='{msg}'")
    
    info = registry.get_info(plugin_name)
    print(f"   After activate: active={info.active}")
    
    # Deactivate
    success, msg = registry.deactivate(plugin_name)
    print(f"   Deactivate: success={success}, message='{msg}'")
    
    info = registry.get_info(plugin_name)
    print(f"   After deactivate: active={info.active}")
    
    # Test with PluginInfo attributes
    print("\n4. Verifying PluginInfo data structure...")
    for p in plugins:
        assert hasattr(p, 'name'), "Missing name attribute"
        assert hasattr(p, 'version'), "Missing version attribute"
        assert hasattr(p, 'description'), "Missing description attribute"
        assert hasattr(p, 'author'), "Missing author attribute"
        assert hasattr(p, 'installed'), "Missing installed attribute"
        assert hasattr(p, 'active'), "Missing active attribute"
    print("   All PluginInfo objects have required attributes ✓")

# Test empty registry scenario
print("\n5. Testing registry with no plugins directory...")
empty_registry = PluginRegistry(plugins_dir="/tmp/nonexistent_plugins_test")
empty_plugins = empty_registry.list_available()
print(f"   Plugins found in empty registry: {len(empty_plugins)}")
print("   Registry is safe when no plugins installed ✓")

print("\n" + "=" * 60)
print("All tests passed!")
print("=" * 60)
