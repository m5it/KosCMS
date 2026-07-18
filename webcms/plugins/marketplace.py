"""
Plugin Marketplace

Plugin registry and management system.
"""

import json
import os
import shutil
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from packaging.version import Version, parse as parse_version
from webcms import __version__


@dataclass
class PluginInfo:
    """Plugin metadata."""
    name: str
    version: str
    description: str
    author: str
    min_cms_version: str
    max_cms_version: Optional[str] = None
    dependencies: List[str] = None
    tags: List[str] = None
    download_url: Optional[str] = None
    installed: bool = False
    active: bool = False
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []


class PluginRegistry:
    """Plugin registry and marketplace manager."""
    
    REGISTRY_FILE = "plugin_registry.json"
    CMS_VERSION = __version__  # Current WebCMS version
    
    def __init__(self, registry_path: str = None, plugins_dir: str = None):
        self.registry_path = Path(registry_path or self.REGISTRY_FILE)
        # Use webcms/plugins as the default plugins directory
        webcms_root = Path(__file__).parent.parent
        self.plugins_dir = Path(plugins_dir or webcms_root / "plugins")
        self.plugins_dir.mkdir(exist_ok=True)
        self._registry: Dict[str, PluginInfo] = {}
        self._load_registry()
        # Auto-discover plugins from filesystem
        self._discover_installed_plugins()
    
    def _discover_installed_plugins(self):
        """Discover plugins from the filesystem and sync with registry."""
        try:
            # Look for plugin directories with plugin.yaml or __init__.py
            if not self.plugins_dir.exists():
                return
            
            for item in self.plugins_dir.iterdir():
                if not item.is_dir():
                    continue
                if item.name.startswith('_') or item.name == '__pycache__':
                    continue
                
                plugin_name = item.name
                
                # Check for plugin.yaml
                config_file = item / "plugin.yaml"
                info_file = item / "plugin.json"
                
                plugin_data = {
                    'name': plugin_name,
                    'version': '1.0.0',
                    'description': f'Plugin: {plugin_name}',
                    'author': 'Unknown',
                    'min_cms_version': '1.0.0',
                    'max_cms_version': None,
                    'dependencies': [],
                    'tags': [],
                    'installed': True,
                    'active': False
                }
                
                # Try to load from plugin.yaml
                if config_file.exists():
                    try:
                        import yaml
                        with open(config_file, 'r') as f:
                            yaml_data = yaml.safe_load(f)
                            if yaml_data:
                                plugin_data.update({
                                    'name': yaml_data.get('name', plugin_name),
                                    'version': yaml_data.get('version', '1.0.0'),
                                    'description': yaml_data.get('description', ''),
                                    'author': yaml_data.get('author', 'Unknown'),
                                    'dependencies': yaml_data.get('requires', []),
                                    'tags': yaml_data.get('tags', []),
                                })
                    except Exception as e:
                        print(f"Error loading plugin.yaml for {plugin_name}: {e}")
                
                # Try to load from plugin.json as fallback
                elif info_file.exists():
                    try:
                        with open(info_file, 'r') as f:
                            json_data = json.load(f)
                            plugin_data.update({
                                'name': json_data.get('name', plugin_name),
                                'version': json_data.get('version', '1.0.0'),
                                'description': json_data.get('description', ''),
                                'author': json_data.get('author', 'Unknown'),
                                'min_cms_version': json_data.get('min_cms_version', '1.0.0'),
                                'max_cms_version': json_data.get('max_cms_version'),
                                'dependencies': json_data.get('dependencies', []),
                                'tags': json_data.get('tags', []),
                            })
                    except Exception as e:
                        print(f"Error loading plugin.json for {plugin_name}: {e}")
                
                # Check if already in registry - preserve active state
                if plugin_name in self._registry:
                    existing = self._registry[plugin_name]
                    plugin_data['active'] = existing.active
                
                # Create PluginInfo and add to registry
                self._registry[plugin_name] = PluginInfo(**plugin_data)
            
            # Save updated registry
            self._save_registry()
            
        except Exception as e:
            print(f"Error discovering plugins: {e}")
    
    def _load_registry(self):
        """Load registry from JSON file."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    for name, info in data.items():
                        self._registry[name] = PluginInfo(**info)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error loading registry: {e}")
                self._registry = {}
    
    def _save_registry(self):
        """Save registry to JSON file."""
        try:
            data = {name: asdict(info) for name, info in self._registry.items()}
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving registry: {e}")
    
    def list_available(self, tag: str = None, 
                       installed_only: bool = False) -> List[PluginInfo]:
        """
        List available plugins.
        
        Args:
            tag: Filter by tag
            installed_only: Show only installed plugins
        
        Returns:
            List of plugin info objects
        """
        plugins = list(self._registry.values())
        
        if installed_only:
            plugins = [p for p in plugins if p.installed]
        
        if tag:
            plugins = [p for p in plugins if tag in p.tags]
        
        # Sort by name
        return sorted(plugins, key=lambda p: p.name)
    
    def get_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get plugin information."""
        return self._registry.get(plugin_name)
    
    def check_compatibility(self, plugin: PluginInfo) -> Tuple[bool, str]:
        """
        Check if plugin is compatible with current CMS version.
        
        Returns:
            Tuple of (is_compatible, reason)
        """
        try:
            current = parse_version(self.CMS_VERSION)
            min_ver = parse_version(plugin.min_cms_version)
            
            if current < min_ver:
                return False, f"Requires WebCMS {plugin.min_cms_version}+"
            
            if plugin.max_cms_version:
                max_ver = parse_version(plugin.max_cms_version)
                if current > max_ver:
                    return False, f"Not compatible with WebCMS {self.CMS_VERSION}"
            
            # Check dependencies
            for dep in plugin.dependencies:
                if dep not in self._registry or not self._registry[dep].installed:
                    return False, f"Requires plugin: {dep}"
            
            return True, "Compatible"
            
        except Exception as e:
            return False, f"Version check error: {e}"
    
    def install(self, plugin_name: str, source_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Install a plugin.
        
        Args:
            plugin_name: Plugin identifier
            source_path: Path to plugin package (zip or directory)
        
        Returns:
            Tuple of (success, message)
        """
        # Check if already installed
        if plugin_name in self._registry and self._registry[plugin_name].installed:
            return False, "Plugin already installed"
        
        # If source provided, install from source
        if source_path:
            return self._install_from_source(plugin_name, source_path)
        
        # Otherwise, check if in registry
        if plugin_name not in self._registry:
            return False, "Plugin not found in registry"
        
        plugin = self._registry[plugin_name]
        
        # Check compatibility
        compatible, reason = self.check_compatibility(plugin)
        if not compatible:
            return False, reason
        
        # Download and install
        if plugin.download_url:
            return self._download_and_install(plugin)
        
        return False, "No installation source available"
    
    def _install_from_source(self, plugin_name: str, source_path: str) -> Tuple[bool, str]:
        """Install plugin from local source."""
        source = Path(source_path)
        
        if not source.exists():
            return False, "Source path does not exist"
        
        target_dir = self.plugins_dir / plugin_name
        
        try:
            if source.is_file() and source.suffix == '.zip':
                # Extract zip
                with zipfile.ZipFile(source, 'r') as z:
                    z.extractall(target_dir)
            elif source.is_dir():
                # Copy directory
                shutil.copytree(source, target_dir)
            else:
                return False, "Invalid source format"
            
            # Load plugin info
            info_path = target_dir / 'plugin.json'
            if info_path.exists():
                with open(info_path) as f:
                    data = json.load(f)
                    plugin = PluginInfo(
                        name=plugin_name,
                        version=data.get('version', '0.0.1'),
                        description=data.get('description', ''),
                        author=data.get('author', ''),
                        min_cms_version=data.get('min_cms_version', '1.0.0'),
                        max_cms_version=data.get('max_cms_version'),
                        dependencies=data.get('dependencies', []),
                        tags=data.get('tags', []),
                        installed=True,
                        active=False
                    )
                    self._registry[plugin_name] = plugin
                    self._save_registry()
            
            return True, "Plugin installed successfully"
            
        except Exception as e:
            return False, f"Installation failed: {e}"
    
    def _download_and_install(self, plugin: PluginInfo) -> Tuple[bool, str]:
        """Download and install plugin from URL."""
        try:
            import urllib.request
            import tempfile
            
            # Download to temp file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                urllib.request.urlretrieve(plugin.download_url, tmp.name)
                
                # Install from downloaded file
                success, msg = self._install_from_source(plugin.name, tmp.name)
                
                # Cleanup
                os.unlink(tmp.name)
                
                return success, msg
                
        except Exception as e:
            return False, f"Download failed: {e}"
    
    def uninstall(self, plugin_name: str) -> Tuple[bool, str]:
        """
        Uninstall a plugin.
        
        Returns:
            Tuple of (success, message)
        """
        if plugin_name not in self._registry:
            return False, "Plugin not found"
        
        plugin = self._registry[plugin_name]
        
        if not plugin.installed:
            return False, "Plugin not installed"
        
        # Check for dependents
        for name, info in self._registry.items():
            if plugin_name in info.dependencies and info.installed:
                return False, f"Required by: {name}"
        
        try:
            # Remove plugin directory
            plugin_dir = self.plugins_dir / plugin_name
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)
            
            # Update registry
            plugin.installed = False
            plugin.active = False
            self._save_registry()
            
            return True, "Plugin uninstalled"
            
        except Exception as e:
            return False, f"Uninstall failed: {e}"
    
    def activate(self, plugin_name: str) -> Tuple[bool, str]:
        """Activate a plugin."""
        if plugin_name not in self._registry:
            return False, "Plugin not found"
        
        plugin = self._registry[plugin_name]
        
        if not plugin.installed:
            return False, "Plugin not installed"
        
        # Check dependencies
        for dep in plugin.dependencies:
            if dep not in self._registry or not self._registry[dep].installed:
                return False, f"Dependency not met: {dep}"
        
        plugin.active = True
        self._save_registry()
        return True, "Plugin activated"
    
    def deactivate(self, plugin_name: str) -> Tuple[bool, str]:
        """Deactivate a plugin."""
        if plugin_name not in self._registry:
            return False, "Plugin not found"
        
        # Check for active dependents
        for name, info in self._registry.items():
            if plugin_name in info.dependencies and info.active:
                return False, f"Required by active plugin: {name}"
        
        self._registry[plugin_name].active = False
        self._save_registry()
        return True, "Plugin deactivated"
    
    def register_plugin(self, plugin: PluginInfo):
        """Register a plugin in the marketplace."""
        self._registry[plugin.name] = plugin
        self._save_registry()
    
    def get_active_plugins(self) -> List[PluginInfo]:
        """Get list of active plugins."""
        return [p for p in self._registry.values() if p.active]


# Global registry instance
_registry_instance: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """Get or create global registry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = PluginRegistry()
    return _registry_instance
