"""
Theme System

Theme discovery, loading, and management with KosDB persistence.
"""

import os
import yaml
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Theme:
    """Theme data class."""
    name: str
    version: str
    description: str
    author: str
    path: Path
    templates_path: Path
    static_path: Path
    config: Dict[str, Any]
    
    def get_template(self, name: str) -> Optional[Path]:
        """Get template file path."""
        template_file = self.templates_path / name
        if template_file.exists():
            return template_file
        return None
    
    def get_static_url(self, path: str) -> str:
        """Get static file URL."""
        return f"/static/themes/{self.name}/{path}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "path": str(self.path),
            "templates_path": str(self.templates_path),
            "static_path": str(self.static_path),
            "config": self.config
        }


class ThemeManager:
    """Theme discovery and management with KosDB support."""
    
    def __init__(self, themes_dir: str = None, db=None):
        # Auto-detect themes directory based on current file location
        if themes_dir is None:
            current_file = Path(__file__).resolve()
            themes_dir = str(current_file.parent / "themes")
        
        self.themes_dir = Path(themes_dir)
        self.db = db
        self.themes: Dict[str, Theme] = {}
        self.active_theme: Optional[Theme] = None
        
        self._ensure_themes_table()
        self._discover_themes()
        self._load_active_theme()
    
    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        cls = getattr(self.db, '__class__', type(self.db))
        cls_name = getattr(cls, '__name__', '')
        return 'KosDB' in cls_name
    
    def _ensure_themes_table(self) -> None:
        """Ensure themes table exists in KosDB."""
        if not self.db or not self._is_kosdb():
            return
        
        try:
            tables = self.db.list_tables()
            if 'themes' in tables:
                return
        except Exception:
            pass
        
        try:
            self.db.execute(
                "CREATE TABLE themes ("
                "id TEXT PRIMARY KEY, "
                "name TEXT, "
                "version TEXT, "
                "description TEXT, "
                "author TEXT, "
                "path TEXT, "
                "config TEXT, "
                "is_active TEXT DEFAULT '0', "
                "created_at TEXT, "
                "updated_at TEXT"
                ")"
            )
        except Exception:
            pass
    
    def _discover_themes(self) -> None:
        """Scan themes directory for themes."""
        if not self.themes_dir.exists():
            # Create default themes directory
            try:
                self.themes_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            return
        
        discovered_themes = []
        
        for item in self.themes_dir.iterdir():
            if item.is_dir():
                theme = self._load_theme(item)
                if theme:
                    discovered_themes.append(theme)
                    self.themes[theme.name] = theme
        
        # Sync to KosDB if available
        if self.db and self._is_kosdb():
            self._sync_themes_to_kosdb(discovered_themes)
    
    def _sync_themes_to_kosdb(self, themes: List[Theme]) -> None:
        """Sync discovered themes to KosDB."""
        if not self.db or not self._is_kosdb():
            return
        
        self._ensure_themes_table()
        
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        
        for theme in themes:
            # Check if theme exists in DB
            try:
                result = self.db.query(f"SELECT id FROM themes WHERE name='{theme.name}'")
                
                if result.get('rows'):
                    # Update existing
                    self.db.execute(
                        f"UPDATE themes SET "
                        f"version='{theme.version}', "
                        f"description='{theme.description}', "
                        f"author='{theme.author}', "
                        f"path='{str(theme.path)}', "
                        f"config='{json.dumps(theme.config)}', "
                        f"updated_at='{now}' "
                        f"WHERE name='{theme.name}'"
                    )
                else:
                    # Insert new
                    theme_id = f"theme_{theme.name}"
                    self.db.execute(
                        f"INSERT INTO themes (id, name, version, description, author, path, config, is_active, created_at, updated_at) "
                        f"VALUES ("
                        f"'{theme_id}', "
                        f"'{theme.name}', "
                        f"'{theme.version}', "
                        f"'{theme.description}', "
                        f"'{theme.author}', "
                        f"'{str(theme.path)}', "
                        f"'{json.dumps(theme.config)}', "
                        f"'0', "
                        f"'{now}', "
                        f"'{now}'"
                        f")"
                    )
            except Exception:
                pass
    
    def _load_theme(self, theme_path: Path) -> Optional[Theme]:
        """
        Load theme from directory.
        
        Args:
            theme_path: Path to theme directory
        
        Returns:
            Theme object or None
        """
        # Try theme.yaml first, then theme.json
        config_file = theme_path / "theme.yaml"
        if not config_file.exists():
            config_file = theme_path / "theme.json"
        
        if not config_file.exists():
            return None
        
        try:
            if config_file.suffix == '.yaml':
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f) or {}
            else:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            
            return Theme(
                name=config.get("name", theme_path.name),
                version=config.get("version", "1.0.0"),
                description=config.get("description", ""),
                author=config.get("author", "Unknown"),
                path=theme_path,
                templates_path=theme_path / "templates",
                static_path=theme_path / "static",
                config=config
            )
        except Exception:
            return None
    
    def _load_active_theme(self) -> None:
        """Load active theme from KosDB or default."""
        # Try KosDB first
        if self.db and self._is_kosdb():
            try:
                result = self.db.query("SELECT name FROM themes WHERE is_active='1' LIMIT 1")
                if result.get('rows'):
                    theme_name = result['rows'][0].get('name')
                    if theme_name and theme_name in self.themes:
                        self.active_theme = self.themes[theme_name]
                        return
            except Exception:
                pass
        
        # Default to first theme or None
        if self.themes:
            self.active_theme = next(iter(self.themes.values()))
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """Get theme by name."""
        return self.themes.get(name)
    
    def activate(self, name: str) -> bool:
        """
        Activate theme by name (alias for set_active_theme).
        
        Args:
            name: Theme name
        
        Returns:
            True if theme was activated
        """
        return self.set_active_theme(name)
    
    def set_active_theme(self, name: str) -> bool:
        """
        Set active theme with persistence.
        
        Args:
            name: Theme name
        
        Returns:
            True if theme exists and was activated
        """
        theme = self.get_theme(name)
        if not theme:
            return False
        
        self.active_theme = theme
        
        # Persist to KosDB if available
        if self.db and self._is_kosdb():
            try:
                # Deactivate all themes
                self.db.execute("UPDATE themes SET is_active='0'")
                # Activate selected theme
                self.db.execute(f"UPDATE themes SET is_active='1' WHERE name='{name}'")
            except Exception:
                pass
        
        return True
    
    def deactivate(self, name: str) -> bool:
        """
        Deactivate a theme.
        
        Args:
            name: Theme name
        
        Returns:
            True if theme was deactivated
        """
        theme = self.get_theme(name)
        if not theme:
            return False
        
        if self.active_theme and self.active_theme.name == name:
            self.active_theme = None
        
        # Update KosDB if available
        if self.db and self._is_kosdb():
            try:
                self.db.execute(f"UPDATE themes SET is_active='0' WHERE name='{name}'")
            except Exception:
                pass
        
        return True
    
    def get_active_theme(self) -> Optional[Theme]:
        """Get currently active theme."""
        return self.active_theme
    
    def list_themes(self) -> List[Dict[str, Any]]:
        """List all available themes with active status."""
        result = []
        active_name = self.active_theme.name if self.active_theme else None
        
        for theme in self.themes.values():
            result.append({
                "id": theme.name,
                "name": theme.name,
                "version": theme.version,
                "description": theme.description,
                "author": theme.author,
                "active": theme.name == active_name
            })
        
        return result
    
    def render(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """
        Render template from active theme.
        
        Args:
            template_name: Template name
            context: Template variables
        
        Returns:
            Rendered HTML
        """
        if not self.active_theme:
            raise RuntimeError("No active theme set")
        
        from .engine import TemplateEngine
        
        engine = TemplateEngine([str(self.active_theme.templates_path)], db=self.db)
        return engine.render(template_name, context)
    
    def get_template_dirs(self) -> List[str]:
        """Get all template directories for loader."""
        dirs = []
        
        # Active theme first
        if self.active_theme:
            dirs.append(str(self.active_theme.templates_path))
        
        # Base templates
        base_path = self.themes_dir.parent / "base"
        if base_path.exists():
            dirs.append(str(base_path))
        
        return dirs
    
    def install_theme(self, theme_path: str) -> Optional[Theme]:
        """
        Install theme from path.
        
        Args:
            theme_path: Path to theme directory
        
        Returns:
            Installed theme or None
        """
        path = Path(theme_path)
        if not path.exists():
            return None
        
        theme = self._load_theme(path)
        if theme:
            self.themes[theme.name] = theme
            
            # Sync to KosDB
            if self.db and self._is_kosdb():
                self._sync_themes_to_kosdb([theme])
        
        return theme
    
    def uninstall_theme(self, name: str) -> bool:
        """
        Uninstall theme.
        
        Args:
            name: Theme name
        
        Returns:
            True if theme was uninstalled
        """
        theme = self.themes.pop(name, None)
        if not theme:
            return False
        
        # Deactivate if active
        if self.active_theme and self.active_theme.name == name:
            self.active_theme = None
        
        # Remove from KosDB
        if self.db and self._is_kosdb():
            try:
                self.db.execute(f"DELETE FROM themes WHERE name='{name}'")
            except Exception:
                pass
        
        return True


# Global singleton
_theme_manager_instance = None


def get_theme_manager(themes_dir: str = None, db=None) -> ThemeManager:
    """Get or create global ThemeManager."""
    global _theme_manager_instance
    if _theme_manager_instance is None:
        _theme_manager_instance = ThemeManager(themes_dir=themes_dir, db=db)
    return _theme_manager_instance
