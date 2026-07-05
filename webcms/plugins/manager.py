"""
Plugin Manager

Discovery, loading, and lifecycle management.
"""

import os
import sys
import yaml
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import PluginBase, PluginConfig
from .hooks import HookManager


class PluginManager:
    """Plugin discovery and management."""
    
    def __init__(self, plugins_dir: str, hook_manager: HookManager):
        self.plugins_dir = Path(plugins_dir)
        self.hook_manager = hook_manager
        self._plugins: Dict[str, PluginBase] = {}
        self._configs: Dict[str, PluginConfig] = {}
        self._loaded: Dict[str, bool] = {}
    
    def discover(self) -> List[PluginConfig]:
        """
        Discover available plugins.
        
        Returns:
            List of plugin configurations
        """
        configs = []
        
        if not self.plugins_dir.exists():
            return configs
        
        for item in self.plugins_dir.iterdir():
            if item.is_dir():
                config = self._load_config(item)
                if config:
                    configs.append(config)
                    self._configs[config.name] = config
        
        return configs
    
    def _load_config(self, plugin_dir: Path) -> Optional[PluginConfig]:
        """Load plugin configuration."""
        config_file = plugin_dir / "plugin.yaml"
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
            
            return PluginConfig(
                name=data.get("name", plugin_dir.name),
                version=data.get("version", "1.0.0"),
                description=data.get("description", ""),
                author=data.get("author", ""),
                requires=data.get("requires", []),
                permissions=data.get("permissions", [])
            )
        except Exception as e:
            print(f"Error loading plugin config from {plugin_dir}: {e}")
            return None
    
    def load(self, name: str) -> Optional[PluginBase]:
        """
        Load plugin by name.
        
        Args:
            name: Plugin name
        
        Returns:
            Plugin instance or None
        """
        if name in self._loaded:
            return self._plugins.get(name)
        
        config = self._configs.get(name)
        if not config:
            return None
        
        # Check dependencies
        for req in config.requires:
            if req not in self._loaded:
                # Auto-load dependency
                self.load(req)
        
        # Import plugin module
        plugin_dir = self.plugins_dir / name
        init_file = plugin_dir / "__init__.py"
        
        if not init_file.exists():
            return None
        
        try:
            # Add to path
            if str(plugin_dir.parent) not in sys.path:
                sys.path.insert(0, str(plugin_dir.parent))
            
            # Import
            module = importlib.import_module(name)
            
            # Find plugin class
            plugin_class = getattr(module, "Plugin", None)
            if plugin_class is None:
                # Look for subclasses
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, PluginBase) and 
                        attr != PluginBase):
                        plugin_class = attr
                        break
            
            if plugin_class:
                # Instantiate
                plugin = plugin_class(config)
                plugin.register()
                
                self._plugins[name] = plugin
                self._loaded[name] = False  # Not yet activated
                
                return plugin
                
        except Exception as e:
            print(f"Error loading plugin {name}: {e}")
        
        return None
    
    def activate(self, name: str) -> bool:
        """
        Activate plugin.
        
        Args:
            name: Plugin name
        
        Returns:
            True if activated
        """
        plugin = self._plugins.get(name)
        if not plugin:
            return False
        
        if self._loaded.get(name):
            return True  # Already active
        
        try:
            if plugin.activate():
                self._loaded[name] = True
                
                # Register plugin hooks
                for event, hooks in plugin._hooks.items():
                    for hook in hooks:
                        self.hook_manager.register(event, hook)
                
                return True
        except Exception as e:
            print(f"Error activating plugin {name}: {e}")
        
        return False
    
    def deactivate(self, name: str) -> bool:
        """Deactivate plugin."""
        plugin = self._plugins.get(name)
        if not plugin:
            return False
        
        try:
            plugin.deactivate()
            self._loaded[name] = False
            
            # Unregister hooks
            for event, hooks in plugin._hooks.items():
                for hook in hooks:
                    self.hook_manager.unregister(event, hook)
            
            return True
        except Exception as e:
            print(f"Error deactivating plugin {name}: {e}")
        
        return False
    
    def get_active_plugins(self) -> List[PluginBase]:
        """Get list of active plugins."""
        return [
            self._plugins[name] 
            for name, active in self._loaded.items() 
            if active
        ]
    
    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get plugin by name."""
        return self._plugins.get(name)
    
    def is_active(self, name: str) -> bool:
        """Check if plugin is active."""
        return self._loaded.get(name, False)