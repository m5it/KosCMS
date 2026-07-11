
"""
Tests for Plugin Marketplace (v1.1.0)

Plugin registry and management.
"""

import pytest
import tempfile
from pathlib import Path

from webcms.plugins.marketplace import (
    PluginRegistry, 
    PluginInfo,
    get_registry
)


class TestPluginInfo:
    """Test plugin info dataclass."""
    
    def test_plugin_info_creation(self):
        """Test PluginInfo creation."""
        plugin = PluginInfo(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            min_cms_version="1.0.0"
        )
        
        assert plugin.name == "test-plugin"
        assert plugin.version == "1.0.0"
        assert plugin.installed is False


class TestPluginRegistry:
    """Test plugin registry."""
    
    @pytest.fixture
    def registry(self):
        """Create test registry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = PluginRegistry(
                registry_path=f"{tmpdir}/registry.json",
                plugins_dir=f"{tmpdir}/plugins"
            )
            yield reg
    
    def test_register_plugin(self, registry):
        """Test plugin registration."""
        plugin = PluginInfo(
            name="test-plugin",
            version="1.0.0",
            description="Test",
            author="Author",
            min_cms_version="1.0.0"
        )
        
        registry.register_plugin(plugin)
        
        retrieved = registry.get_info("test-plugin")
        assert retrieved is not None
        assert retrieved.name == "test-plugin"
    
    def test_list_available(self, registry):
        """Test listing plugins."""
        plugin = PluginInfo(
            name="test-plugin",
            version="1.0.0",
            description="Test",
            author="Author",
            min_cms_version="1.0.0",
            tags=["test"]
        )
        
        registry.register_plugin(plugin)
        plugins = registry.list_available()
        
        assert len(plugins) >= 1
        assert any(p.name == "test-plugin" for p in plugins)
    
    def test_check_compatibility(self, registry):
        """Test version compatibility."""
        plugin = PluginInfo(
            name="test-plugin",
            version="1.0.0",
            description="Test",
            author="Author",
            min_cms_version="1.0.0",
            max_cms_version="2.0.0"
        )
        
        compatible, reason = registry.check_compatibility(plugin)
        assert compatible is True
    
    def test_check_compatibility_too_new(self, registry):
        """Test compatibility with future version."""
        plugin = PluginInfo(
            name="test-plugin",
            version="1.0.0",
            description="Test",
            author="Author",
            min_cms_version="99.0.0"
        )
        
        compatible, reason = registry.check_compatibility(plugin)
        assert compatible is False
    
    def test_get_active_plugins(self, registry):
        """Test getting active plugins."""
        plugin = PluginInfo(
            name="active-plugin",
            version="1.0.0",
            description="Test",
            author="Author",
            min_cms_version="1.0.0",
            installed=True,
            active=True
        )
        
        registry.register_plugin(plugin)
        active = registry.get_active_plugins()
        
        assert len(active) == 1
        assert active[0].name == "active-plugin"


class TestGlobalRegistry:
    """Test global registry singleton."""
    
    def test_get_registry_singleton(self):
        """Test singleton pattern."""
        reg1 = get_registry()
        reg2 = get_registry()
        
        assert reg1 is reg2
