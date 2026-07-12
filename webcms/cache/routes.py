"""
Cache analytics dashboard routes.
"""

from webcms.core.request import Request
from webcms.core.response import Response


def register_cache_routes(app, cache_manager):
    """Register cache analytics routes."""

    @app.route("/admin/cache/analytics", methods=["GET"])
    def cache_analytics(request: Request):
        return Response.json(cache_manager._analytics.get_dashboard_data())

    @app.route("/admin/cache/invalidate", methods=["POST"])
    async def cache_invalidate(request: Request):
        data = request.json or {}
        pattern = data.get("pattern", "*")
        count = await cache_manager.invalidate_pattern(pattern)
        if cache_manager._analytics:
            await cache_manager._analytics.record_invalidation(count)
        return Response.json({"invalidated": count})

    @app.route("/admin/cache/warm", methods=["POST"])
    async def cache_warm(request: Request):
        results = await cache_manager.warm_cache()
        return Response.json({"warmed": len(results), "results": results})
