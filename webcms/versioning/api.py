"""
Version API endpoints for WebCMS

REST API for content versioning operations.
"""

from webcms.core.request import Request
from webcms.core.response import Response
from .manager import VersionManager


class VersionAPI:
    """Version API endpoints."""

    def __init__(self, version_manager=None):
        self.manager = version_manager or VersionManager()

    async def list_versions(self, request: Request, content_type: str, content_id: str):
        """List versions for content."""
        try:
            versions = await self.manager.list_versions(content_id, content_type)
            return Response.json({
                "content_id": content_id,
                "content_type": content_type,
                "versions": [v.to_dict() for v in versions]
            })
        except Exception as e:
            return Response.error(str(e), 500)

    async def create_version(self, request: Request, content_type: str, content_id: str):
        """Create new version."""
        data = request.json or {}
        if not data:
            return Response.error("No data provided", 400)

        try:
            version = await self.manager.create_version(
                content_id=content_id,
                content_type=content_type,
                data=data.get("data", {}),
                user_id=data.get("user_id"),
                username=data.get("username"),
                comment=data.get("comment")
            )
            return Response.json(version.to_dict(), 201)
        except Exception as e:
            return Response.error(str(e), 500)

    async def get_version(self, request: Request, version_id: str):
        """Get version by ID."""
        try:
            version = await self.manager.get_version(version_id)
            if not version:
                return Response.not_found()
            return Response.json(version.to_dict())
        except Exception as e:
            return Response.error(str(e), 500)

    async def compare_versions(self, request: Request):
        """Compare two versions."""
        version_id1 = request.get_param("v1")
        version_id2 = request.get_param("v2")
        field = request.get_param("field", "content")

        if not version_id1 or not version_id2:
            return Response.error("Both v1 and v2 required", 400)

        try:
            result = await self.manager.compare_versions(version_id1, version_id2, field)
            return Response.json(result)
        except Exception as e:
            return Response.error(str(e), 500)

    async def rollback(self, request: Request, content_type: str, content_id: str):
        """Rollback to specific version."""
        data = request.json or {}
        version_number = data.get("version_number")

        if not version_number:
            return Response.error("version_number required", 400)

        try:
            version = await self.manager.rollback(
                content_id=content_id,
                content_type=content_type,
                version_number=int(version_number),
                user_id=data.get("user_id"),
                username=data.get("username"),
                comment=data.get("comment")
            )
            if not version:
                return Response.not_found()
            return Response.json(version.to_dict())
        except Exception as e:
            return Response.error(str(e), 500)

    async def audit_trail(self, request: Request, content_type: str, content_id: str):
        """Get audit trail."""
        try:
            trail = await self.manager.get_audit_trail(content_id, content_type)
            return Response.json({
                "content_id": content_id,
                "content_type": content_type,
                "trail": trail
            })
        except Exception as e:
            return Response.error(str(e), 500)


def register_version_api(app, version_manager=None):
    """Register version API routes."""
    api = VersionAPI(version_manager)

    @app.route("/api/v1/<content_type>/<content_id>/versions", methods=["GET"])
    def list_versions(request, content_type, content_id):
        return api.list_versions(request, content_type, content_id)

    @app.route("/api/v1/<content_type>/<content_id>/versions", methods=["POST"])
    def create_version(request, content_type, content_id):
        return api.create_version(request, content_type, content_id)

    @app.route("/api/v1/versions/<version_id>", methods=["GET"])
    def get_version(request, version_id):
        return api.get_version(request, version_id)

    @app.route("/api/v1/versions/compare", methods=["GET"])
    def compare_versions(request):
        return api.compare_versions(request)

    @app.route("/api/v1/<content_type>/<content_id>/rollback", methods=["POST"])
    def rollback(request, content_type, content_id):
        return api.rollback(request, content_type, content_id)

    @app.route("/api/v1/<content_type>/<content_id>/audit", methods=["GET"])
    def audit_trail(request, content_type, content_id):
        return api.audit_trail(request, content_type, content_id)
