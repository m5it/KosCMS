"""
Admin Dashboard

React-based admin interface with REST API.
"""

from .api import create_api
from .routes import admin_routes

__all__ = ["create_api", "admin_routes"]