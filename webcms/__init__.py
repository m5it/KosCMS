"""
WebCMS - Modern Python Content Management System

A production-ready CMS with HTTPS, plugin architecture, and template system.
"""

__version__ = "1.3.0"
__author__ = "WebCMS Team"

from .core.application import Application
from .core.request import Request
from .core.response import Response

__all__ = ["Application", "Request", "Response"]
