"""
Tenant-aware database routing and request context.
"""

from contextvars import ContextVar
from typing import Optional


current_tenant = ContextVar("current_tenant", default=None)


class TenantRouter:
    """Routes database queries to tenant-specific schemas."""

    def __init__(self, default_schema="public"):
        self.default_schema = default_schema

    def get_current_schema(self) -> str:
        """Get schema for current tenant context."""
        tenant = current_tenant.get()
        if tenant:
            return tenant.schema_name
        return self.default_schema

    def set_tenant(self, tenant):
        """Set current tenant in context."""
        token = current_tenant.set(tenant)
        return token

    def reset_tenant(self, token):
        """Reset tenant context."""
        current_tenant.reset(token)

    def get_table_name(self, table: str) -> str:
        """Get fully qualified table name."""
        schema = self.get_current_schema()
        return f'"{schema}"."{table}"'


class TenantMiddleware:
    """Middleware to set tenant from request."""

    def __init__(self, tenant_manager):
        self.manager = tenant_manager

    async def process_request(self, request):
        """Set tenant based on host header."""
        host = request.headers.get("host", "localhost")
        tenant = await self.manager.get_tenant_by_domain(host)
        if tenant:
            token = self.manager.router.set_tenant(tenant)
            request.tenant_token = token
        return request

    async def process_response(self, request, response):
        """Reset tenant context."""
        if hasattr(request, "tenant_token"):
            self.manager.router.reset_tenant(request.tenant_token)
        return response
