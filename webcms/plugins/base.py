"""
Plugin Base Classes

Abstract base for all plugins.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Callable, Any, Optional


@dataclass
class PluginConfig:
    """Plugin configuration."""
    name: str
    version: str
    description: str = ""
    author: str = ""
    requires: List[str] = None
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.requires is None:
            self.requires = []
        if self.permissions is None:
            self.permissions = []


class PluginBase(ABC):
    """Abstract base class for plugins."""
    
    def __init__(self, config: PluginConfig):
        self.config = config
        self.is_active = False
        self._hooks: Dict[str, List[Callable]] = {}
    
    @abstractmethod
    def register(self) -> None:
        """Register plugin hooks."""
        pass
    
    @abstractmethod
    def activate(self) -> bool:
        """Activate plugin."""
        pass
    
    @abstractmethod
    def deactivate(self) -> None:
        """Deactivate plugin."""
        pass
    
    def register_hook(self, event: str, callback: Callable) -> None:
        """Register hook callback."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)
    
    def get_hooks(self, event: str) -> List[Callable]:
        """Get hooks for event."""
        return self._hooks.get(event, [])
    
    def on_install(self) -> bool:
        """Called when plugin is installed."""
        return True
    
    def on_uninstall(self) -> bool:
        """Called when plugin is uninstalled."""
        return True
    
    def get_admin_routes(self) -> List[Dict[str, Any]]:
        """Get admin panel routes."""
        return []
    
    def get_widgets(self) -> List[Dict[str, Any]]:
        """Get dashboard widgets."""
        return []
    
    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Get admin menu items."""
        return []