"""
Theme System

Theme discovery, loading, and management.
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass


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


class ThemeManager:
    """Theme discovery and management."""
    
    def __init__(self, themes_dir: str):
        self.themes_dir = Path(themes_dir)
        self.themes: Dict[str, Theme] = {}
        self.active_theme: Optional[Theme] = None
        
        self._discover_themes()
    
    def _discover_themes(self) -> None:
        """Scan themes directory for themes."""
        if not self.themes_dir.exists():
            return
        
        for item in self.themes_dir.iterdir():
            if item.is_dir():
                theme = self._load_theme(item)
                if theme:
                    self.themes[theme.name] = theme
    
    def _load_theme(self, theme_path: Path) -> Optional[Theme]:
        """
        Load theme from directory.
        
        Args:
            theme_path: Path to theme directory
        
        Returns:
            Theme object or None
        """
        config_file = theme_path / "theme.yaml"
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
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
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """Get theme by name."""
        return self.themes.get(name)
    
    def set_active_theme(self, name: str) -> bool:
        """
        Set active theme.
        
        Args:
            name: Theme name
        
        Returns:
            True if theme exists and was activated
        """
        theme = self.get_theme(name)
        if theme:
            self.active_theme = theme
            return True
        return False
    
    def get_active_theme(self) -> Optional[Theme]:
        """Get currently active theme."""
        return self.active_theme
    
    def list_themes(self) -> List[Dict[str, Any]]:
        """List all available themes."""
        return [
            {
                "name": t.name,
                "version": t.version,
                "description": t.description,
                "author": t.author
            }
            for t in self.themes.values()
        ]
    
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
        
        engine = TemplateEngine([str(self.active_theme.templates_path)])
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