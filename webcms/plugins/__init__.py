"""
WebCMS Plugin System

Hook-based plugin architecture with secure sandbox.
"""

from .base import PluginBase, PluginConfig
from .manager import PluginManager
from .hooks import HookManager, HookType

__all__ = [
    "PluginBase",
    "PluginConfig", 
    "PluginManager",
    "HookManager",
    "HookType"
]