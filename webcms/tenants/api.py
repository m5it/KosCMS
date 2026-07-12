"""
Tenant management API endpoints.
"""

from webcms.core.request import Request
from webcms.core.response import Response
from .manager import TenantManager
from .models import TenantQuota


class TenantAPI:
    """Tenant management API."""

    def __init__(self, tenant_manager=None):
        self.manager = tenant_manager or TenantManager()

    async def list_tenants(self, request: Request):
        """List all tenants."""
        tenants = await self.manager.list_tenants()
        return Response.json({"tenants": [t.to_dict() for t in tenants]})

    async def create_tenant(self, request: Request):
        """Create tenant."""
        data = request.json or {}
        required = ["name", "slug", "domain"]
        for field in required:
            if field not in data:
                return Response.error(f"Missing {field}", 400)

        quotas = None
        if "quotas" in data:
            quotas = TenantQuota(**data["quotas"])

        tenant = await self.manager.create_tenant(
            name=data["name"],
            slug=data["slug"],
            domain=data["domain"],
            schema_name=data.get("schema_name"),
            theme=data.get("theme", "default"),
            quotas=quotas
        )
        return Response.json(tenant.to_dict(), 201)

    async def get_tenant(self, request: Request, tenant_id: str):
        """Get tenant by ID."""
        tenant = await self.manager.get_tenant(tenant_id)
        if not tenant:
            return Response.not_found()
        return Response.json(tenant.to_dict())

    async def update_tenant(self, request: Request, tenant_id: str):
        """Update tenant."""
        data = request.json or {}
        tenant = await self.manager.update_tenant(tenant_id, data)
        if not tenant:
            return Response.not_found()
        return Response.json(tenant.to_dict())

    async def delete_tenant(self, request: Request, tenant_id: str):
        """Delete tenant."""
        success = await self.manager.delete_tenant(tenant_id)
        if not success:
            return Response.not_found()
        return Response.json({"deleted": True})

    async def set_theme(self, request: Request, tenant_id: str):
        """Set tenant theme."""
        data = request.json or {}
        theme = data.get("theme")
        if not theme:
            return Response.error("theme required", 400)
        tenant = await self.manager.set_tenant_theme(tenant_id, theme)
        if not tenant:
            return Response.not_found()
        return Response.json(tenant.to_dict())

    async def add_plugin(self, request: Request, tenant_id: str):
        """Add plugin to tenant."""
        data = request.json or {}
        plugin_id = data.get("plugin_id")
        if not plugin_id:
            return Response.error("plugin_id required", 400)
        tenant = await self.manager.add_tenant_plugin(tenant_id, plugin_id)
        if not tenant:
            return Response.not_found()
        return Response.json(tenant.to_dict())

    async def share_content(self, request: Request):
        """Share content across tenants."""
        data = request.json or {}
        required = ["source_tenant_id", "target_tenant_id", "content_id"]
        for field in required:
            if field not in data:
                return Response.error(f"Missing {field}", 400)
        result = await self.manager.share_content(
            data["source_tenant_id"],
            data["target_tenant_id"],
            data["content_id"],
            data.get("content_type", "post")
        )
        return Response.json(result)

    async def get_analytics(self, request: Request, tenant_id: str):
        """Get tenant analytics."""
        analytics = await self.manager.get_analytics(tenant_id)
        if "error" in analytics:
            return Response.error(analytics["error"], 404)
        return Response.json(analytics)

    async def backup_tenant(self, request: Request, tenant_id: str):
        """Backup tenant."""
        backup = await self.manager.backup_tenant(tenant_id)
        if "error" in backup:
            return Response.error(backup["error"], 404)
        return Response.json(backup)

    async def restore_tenant(self, request: Request, tenant_id: str):
        """Restore tenant."""
        data = request.json or {}
        if "data" not in data:
            return Response.error("data required", 400)
        tenant = await self.manager.restore_tenant(tenant_id, data["data"])
        if not tenant:
            return Response.error("Restore failed", 400)
        return Response.json(tenant.to_dict())

    async def check_quota(self, request: Request, tenant_id: str, resource: str):
        """Check quota."""
        quota = await self.manager.check_quota(tenant_id, resource)
        if "error" in quota:
            return Response.error(quota["error"], 404)
        return Response.json(quota)


def register_tenant_api(app, tenant_manager=None):
    """Register tenant API routes."""
    api = TenantAPI(tenant_manager)

    @app.route("/api/v1/tenants", methods=["GET"])
    def list_tenants(request):
        return api.list_tenants(request)

    @app.route("/api/v1/tenants", methods=["POST"])
    def create_tenant(request):
        return api.create_tenant(request)

    @app.route("/api/v1/tenants/<tenant_id>", methods=["GET"])
    def get_tenant(request, tenant_id):
        return api.get_tenant(request, tenant_id)

    @app.route("/api/v1/tenants/<tenant_id>", methods=["PUT"])
    def update_tenant(request, tenant_id):
        return api.update_tenant(request, tenant_id)

    @app.route("/api/v1/tenants/<tenant_id>", methods=["DELETE"])
    def delete_tenant(request, tenant_id):
        return api.delete_tenant(request, tenant_id)

    @app.route("/api/v1/tenants/<tenant_id>/theme", methods=["PUT"])
    def set_theme(request, tenant_id):
        return api.set_theme(request, tenant_id)

    @app.route("/api/v1/tenants/<tenant_id>/plugins", methods=["POST"])
    def add_plugin(request, tenant_id):
        return api.add_plugin(request, tenant_id)

    @app.route("/api/v1/tenants/share", methods=["POST"])
    def share_content(request):
        return api.share_content(request)

    @app.route("/api/v1/tenants/<tenant_id>/analytics", methods=["GET"])
    def get_analytics(request, tenant_id):
        return api.get_analytics(request, tenant_id)

    @app.route("/api/v1/tenants/<tenant_id>/backup", methods=["POST"])
    def backup_tenant(request, tenant_id):
        return api.backup_tenant(request, tenant_id)

    @app.route("/api/v1/tenants/<tenant_id>/restore", methods=["POST"])
    def restore_tenant(request, tenant_id):
        return api.restore_tenant(request, tenant_id)

    @app.route("/api/v1/tenants/<tenant_id>/quota/<resource>", methods=["GET"])
    def check_quota(request, tenant_id, resource):
        return api.check_quota(request, tenant_id, resource)
