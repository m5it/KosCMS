"""
WebCMS Template System

Jinja2-based templating with theme support and asset pipeline.
"""

from .engine import TemplateEngine
from .theme import ThemeManager, Theme
from .filters import register_filters

__all__ = ["TemplateEngine", "ThemeManager", "Theme", "register_filters"]