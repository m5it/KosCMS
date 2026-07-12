"""
GraphQL API for WebCMS

Provides GraphQL queries, mutations, and subscriptions.
"""

from .schema import schema
from .middleware import ComplexityMiddleware, PermissionMiddleware

__all__ = ["schema", "ComplexityMiddleware", "PermissionMiddleware"]
