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
    
    def __init__(self, plugins_dir: str = "plugins", hook_manager: HookManager = None, db=None):
        self.plugins_dir = Path(plugins_dir)
        self.hook_manager = hook_manager or HookManager()
        self.db = db
        self._plugins: Dict[str, PluginBase] = {}
        self._configs: Dict[str, PluginConfig] = {}
        self._loaded: Dict[str, bool] = {}
    
    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods
    
    def _ensure_tables(self):
        """Ensure plugin tables exist."""
        if not self.db or not self._is_kosdb():
            return
        
        try:
            tables = self.db.list_tables()
        except Exception:
            tables = []
        
        if 'plugins' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE plugins (
                        name TEXT PRIMARY KEY,
                        version TEXT,
                        enabled TEXT DEFAULT '0',
                        config TEXT,
                        installed_at TEXT
                    )
                """)
            except Exception:
                pass
    
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
    
    def load(self, plugin_name: str) -> bool:
        """
        Load a plugin.
        
        Args:
            plugin_name: Name of the plugin to load
        
        Returns:
            True if loaded successfully
        """
        if plugin_name in self._loaded:
            return True
        
        config = self._configs.get(plugin_name)
        if not config:
            return False
        
        try:
            plugin_dir = self.plugins_dir / plugin_name
            module_path = f"webcms.plugins.{plugin_name}"
            
            # Add to path
            sys.path.insert(0, str(plugin_dir.parent))
            
            # Import plugin module
            module = importlib.import_module(f"{plugin_name}.plugin")
            
            # Get plugin class
            plugin_class = getattr(module, 'Plugin', None)
            if not plugin_class:
                return False
            
            # Instantiate
            plugin = plugin_class(config)
            self._plugins[plugin_name] = plugin
            
            # Register hooks
            if self.hook_manager:
                plugin.register_hooks(self.hook_manager)
            
            self._loaded[plugin_name] = True
            return True
            
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    def unload(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        if plugin_name not in self._loaded:
            return False
        
        plugin = self._plugins.get(plugin_name)
        if plugin:
            plugin.shutdown()
        
        del self._plugins[plugin_name]
        del self._loaded[plugin_name]
        return True
    
    def is_loaded(self, plugin_name: str) -> bool:
        """Check if plugin is loaded."""
        return plugin_name in self._loaded
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Get loaded plugin instance."""
        return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[Dict]:
        """List all plugins."""
        return [
            {
                "name": name,
                "version": config.version,
                "description": config.description,
                "author": config.author,
                "loaded": name in self._loaded
            }
            for name, config in self._configs.items()
        ]
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict]:
        """Get plugin information."""
        config = self._configs.get(plugin_name)
        if not config:
            return None
        
        return {
            "name": config.name,
            "version": config.version,
            "description": config.description,
            "author": config.author,
            "requires": config.requires,
            "permissions": config.permissions,
            "loaded": plugin_name in self._loaded
        }
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable plugin."""
        if plugin_name not in self._configs:
            return False
        return self.load(plugin_name)
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable plugin."""
        return self.unload(plugin_name)
    
    def get_hooks(self) -> List[str]:
        """Get registered hook names."""
        if self.hook_manager:
            return self.hook_manager.list_hooks()
        return []
