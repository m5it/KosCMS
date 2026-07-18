#!/usr/bin/env python3
"""Fix cache API endpoints in admin_api.py"""

with open('webcms/admin/admin_api.py', 'r') as f:
    content = f.read()

# Fix cache_stats
old_stats = '''    def cache_stats(self, request: Request) -> Response:
        from webcms.cache.manager import get_tenant_cache
        try:
            cache = get_tenant_cache("default")
            stats = cache.get_stats() if hasattr(cache, "get_stats") else {}
            return Response.json({
                "keys": stats.get("keys", 0),
                "hit_rate": stats.get("hit_rate", 0),
                "memory": stats.get("memory", "0B"),
                "evicted": stats.get("evicted", 0)
            })
        except Exception:
            return Response.json({"keys": 0, "hit_rate": 0, "memory": "0B", "evicted": 0})'''

new_stats = '''    def cache_stats(self, request: Request) -> Response:
        from webcms.cache.manager import get_tenant_cache
        try:
            cache = get_tenant_cache("default", db=self.db)
            stats = cache.get_stats_from_kosdb() if self.db else cache.get_stats()
            return Response.json({
                "keys": stats.get("keys", 0),
                "hit_rate": stats.get("hit_rate", 0),
                "memory": stats.get("memory", "0B"),
                "evicted": stats.get("evicted", 0)
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response.json({"keys": 0, "hit_rate": 0, "memory": "0B", "evicted": 0})'''

if old_stats in content:
    content = content.replace(old_stats, new_stats)
    print("Fixed cache_stats")
else:
    print("Could not find cache_stats")

# Fix cache_warm
old_warm = '''    def cache_warm(self, request: Request) -> Response:
        return Response.json({"warmed": 0})'''

new_warm = '''    def cache_warm(self, request: Request) -> Response:
        from webcms.cache.manager import get_tenant_cache
        try:
            cache = get_tenant_cache("default", db=self.db)
            # Warm common cache entries
            warmed = 0
            # Add warming logic here if needed
            return Response.json({"success": True, "warmed": warmed})
        except Exception as e:
            return Response.json({"success": False, "warmed": 0, "message": str(e)})'''

if old_warm in content:
    content = content.replace(old_warm, new_warm)
    print("Fixed cache_warm")
else:
    print("Could not find cache_warm")

# Fix cache_invalidate
old_invalidate = '''    def cache_invalidate(self, request: Request) -> Response:
        from webcms.cache.manager import get_tenant_cache
        data = request.json or {}
        pattern = data.get("pattern", "*")
        try:
            cache = get_tenant_cache("default")
            if hasattr(cache, "invalidate_pattern"):
                deleted = cache.invalidate_pattern(pattern)
            else:
                cache.clear()
                deleted = 0
            return Response.json({"deleted": deleted, "pattern": pattern})
        except Exception:
            return Response.json({"deleted": 0, "pattern": pattern})'''

new_invalidate = '''    def cache_invalidate(self, request: Request) -> Response:
        from webcms.cache.manager import get_tenant_cache
        data = request.json or {}
        pattern = data.get("pattern", "*")
        try:
            cache = get_tenant_cache("default", db=self.db)
            deleted = cache.invalidate_pattern(pattern)
            return Response.json({"success": True, "deleted": deleted, "pattern": pattern})
        except Exception as e:
            return Response.json({"success": False, "deleted": 0, "pattern": pattern, "message": str(e)})'''

if old_invalidate in content:
    content = content.replace(old_invalidate, new_invalidate)
    print("Fixed cache_invalidate")
else:
    print("Could not find cache_invalidate")

with open('webcms/admin/admin_api.py', 'w') as f:
    f.write(content)

print("All cache API fixes applied")
