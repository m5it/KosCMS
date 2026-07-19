"""
Plugin Marketplace

Plugin registry and management system.
"""

import json
import logging
import os
import shutil
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from packaging.version import Version, parse as parse_version
from webcms import __version__

logger = logging.getLogger("webcms.plugins.marketplace")


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
    
    def __init__(self, registry_path: str = None, plugins_dir: str = None, db=None):
        self.registry_path = Path(registry_path or self.REGISTRY_FILE)
        # Use webcms/plugins as the default plugins directory
        webcms_root = Path(__file__).parent.parent
        self.plugins_dir = Path(plugins_dir or webcms_root / "plugins")
        self.plugins_dir.mkdir(exist_ok=True)
        self.db = db
        self._registry: Dict[str, PluginInfo] = {}
        self._load_registry()
        # Auto-discover plugins from filesystem
        self._discover_installed_plugins()
        # Sync discovered state to KosDB if available
        self._sync_to_kosdb()
    def _is_kosdb(self) -> bool:
        """Check if the provided db is a KosDB instance."""
        if self.db is None:
            return False
        cls = getattr(self.db, '__class__', type(self.db))
        cls_name = getattr(cls, '__name__', '')
        return 'KosDB' in cls_name

    def _ensure_plugins_table(self):
        """Create the plugins table in KosDB if it does not exist."""
        if not self.db or not self._is_kosdb():
            return
        try:
            tables = self.db.list_tables()
            if "plugins" in tables:
                return
        except Exception:
            pass
        try:
            self.db.execute(
                "CREATE TABLE plugins ("
                "    name TEXT PRIMARY KEY,"
                "    version TEXT,"
                "    description TEXT,"
                "    author TEXT,"
                "    min_cms_version TEXT,"
                "    max_cms_version TEXT,"
                "    dependencies TEXT,"
                "    tags TEXT,"
                "    download_url TEXT,"
                "    installed TEXT DEFAULT '0',"
                "    active TEXT DEFAULT '0',"
                "    installed_at TEXT"
                ")"
            )
        except Exception:
            pass

    @staticmethod
    def _sql_escape(value) -> str:
        if value is None:
            return "NULL"
        return str(value).replace("'", "''")

    def _sync_to_kosdb(self):
        """Persist current registry state to KosDB, merging with existing rows."""
        if not self.db or not self._is_kosdb():
            return
        self._ensure_plugins_table()
        for name, info in self._registry.items():
            self._upsert_plugin_kosdb(info)

    def _upsert_plugin_kosdb(self, plugin: PluginInfo):
        """Insert or update a plugin row in KosDB."""
        if not self.db or not self._is_kosdb():
            return
        self._ensure_plugins_table()
        check = self.db.query(f"SELECT name FROM plugins WHERE name='{self._sql_escape(plugin.name)}'")
        exists = not check.get('error') and bool(check.get('rows', []))
        deps = json.dumps(plugin.dependencies) if plugin.dependencies else '[]'
        tags = json.dumps(plugin.tags) if plugin.tags else '[]'
        installed = '1' if plugin.installed else '0'
        active = '1' if plugin.active else '0'
        installed_at = datetime.utcnow().isoformat() if plugin.installed else None
        if exists:
            cmd = (
                f"UPDATE plugins SET "
                f"version='{self._sql_escape(plugin.version)}', "
                f"description='{self._sql_escape(plugin.description)}', "
                f"author='{self._sql_escape(plugin.author)}', "
                f"min_cms_version='{self._sql_escape(plugin.min_cms_version)}', "
                f"max_cms_version='{self._sql_escape(plugin.max_cms_version)}', "
                f"dependencies='{self._sql_escape(deps)}', "
                f"tags='{self._sql_escape(tags)}', "
                f"download_url='{self._sql_escape(plugin.download_url)}', "
                f"installed='{installed}', "
                f"active='{active}' "
                f"WHERE name='{self._sql_escape(plugin.name)}'"
            )
        else:
            cmd = (
                f"INSERT INTO plugins (name, version, description, author, min_cms_version, "
                f"max_cms_version, dependencies, tags, download_url, installed, active, installed_at) "
                f"VALUES ('{self._sql_escape(plugin.name)}', '{self._sql_escape(plugin.version)}', "
                f"'{self._sql_escape(plugin.description)}', '{self._sql_escape(plugin.author)}', "
                f"'{self._sql_escape(plugin.min_cms_version)}', '{self._sql_escape(plugin.max_cms_version)}', "
                f"'{self._sql_escape(deps)}', '{self._sql_escape(tags)}', '{self._sql_escape(plugin.download_url)}', "
                f"'{installed}', '{active}', '{self._sql_escape(installed_at)}')"
            )
        try:
            self.db.execute(cmd)
        except Exception as e:
            logger.warning("Failed to sync plugin %s to KosDB: %s", plugin.name, e)

    def _load_from_kosdb(self):
        """Load plugin state from KosDB into the registry."""
        if not self.db or not self._is_kosdb():
            return
        self._ensure_plugins_table()
        result = self.db.query("SELECT * FROM plugins")
        if result.get('error'):
            return
        for row in result.get('rows', []):
            name = row.get('name')
            if not name:
                continue
            try:
                deps = json.loads(row.get('dependencies') or '[]')
                tags = json.loads(row.get('tags') or '[]')
            except Exception:
                deps, tags = [], []
            info = PluginInfo(
                name=name,
                version=row.get('version', '1.0.0'),
                description=row.get('description', ''),
                author=row.get('author', 'Unknown'),
                min_cms_version=row.get('min_cms_version', '1.0.0'),
                max_cms_version=row.get('max_cms_version'),
                dependencies=deps,
                tags=tags,
                download_url=row.get('download_url'),
                installed=str(row.get('installed')).lower() in ('1', 'true', 'yes'),
                active=str(row.get('active')).lower() in ('1', 'true', 'yes')
            )
            self._registry[name] = info

    
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
                        logger.warning("Error loading plugin.yaml for %s: %s", plugin_name, e)
                
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
                        logger.warning("Error loading plugin.json for %s: %s", plugin_name, e)
                
                # Check if already in registry - preserve active state
                if plugin_name in self._registry:
                    existing = self._registry[plugin_name]
                    plugin_data['active'] = existing.active
                
                # Create PluginInfo and add to registry
                self._registry[plugin_name] = PluginInfo(**plugin_data)
            
            # Save updated registry
            self._save_registry()
            
        except Exception as e:
            logger.warning("Error discovering plugins: %s", e)
    
    def _load_registry(self):
        """Load registry from KosDB (preferred) or JSON file fallback."""
        # Prefer KosDB when available
        self._load_from_kosdb()
        if self._registry:
            return
        # Fallback to filesystem registry
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    for name, info in data.items():
                        self._registry[name] = PluginInfo(**info)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("Error loading registry: %s", e)
                self._registry = {}
    
    def _save_registry(self):
        """Save registry to JSON file and KosDB if available."""
        try:
            data = {name: asdict(info) for name, info in self._registry.items()}
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning("Error saving registry: %s", e)
        # Always sync to KosDB when available
        self._sync_to_kosdb()
    
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


# Global registry cache keyed by db identity
_registry_instances: Dict[int, PluginRegistry] = {}


def get_registry(db=None) -> PluginRegistry:
    """Get or create a PluginRegistry instance for the given db."""
    global _registry_instances
    key = id(db) if db else 0
    if key not in _registry_instances:
        _registry_instances[key] = PluginRegistry(db=db)
    return _registry_instances[key]
