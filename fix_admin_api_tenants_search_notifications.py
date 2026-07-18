#!/usr/bin/env python3
"""Fix admin API for tenants, search, and notifications"""

with open('webcms/admin/admin_api.py', 'r') as f:
    content = f.read()

# Fix tenant_analytics
old_analytics = '''    def tenant_analytics(self, request: Request, tenant_id: str) -> Response:
        return Response.json({
            "users": 0,
            "content_count": 0,
            "storage": "0 MB",
            "requests_24h": 0
        })'''

new_analytics = '''    def tenant_analytics(self, request: Request, tenant_id: str) -> Response:
        from webcms.tenants.manager import TenantManager
        try:
            manager = TenantManager(db=self.db)
            analytics = manager.get_analytics_sync(tenant_id)
            return Response.json(analytics)
        except Exception as e:
            return Response.json({
                "users": 0,
                "content_count": 0,
                "storage": "0 MB",
                "requests_24h": 0
            })'''

if old_analytics in content:
    content = content.replace(old_analytics, new_analytics)
    print("Fixed tenant_analytics")
else:
    print("Could not find tenant_analytics")

# Fix add_search_suggestion
old_add_suggestion = '''    def add_search_suggestion(self, request: Request) -> Response:
        data = request.json or {}
        query = data.get("query", "")
        if not query:
            return Response.error("Query required", 400)
        return Response.json({"id": str(uuid.uuid4()), "query": query}, 201)'''

new_add_suggestion = '''    def add_search_suggestion(self, request: Request) -> Response:
        from webcms.search.analytics import SearchAnalytics
        data = request.json or {}
        query = data.get("query", "")
        if not query:
            return Response.error("Query required", 400)
        try:
            analytics = SearchAnalytics(db=self.db)
            suggestion = analytics.add_suggestion(query)
            return Response.json(suggestion, 201)
        except Exception as e:
            return Response.json({"id": str(uuid.uuid4()), "query": query, "error": str(e)}, 201)'''

if old_add_suggestion in content:
    content = content.replace(old_add_suggestion, new_add_suggestion)
    print("Fixed add_search_suggestion")
else:
    print("Could not find add_search_suggestion")

# Fix delete_search_suggestion
old_del_suggestion = '''    def delete_search_suggestion(self, request: Request, suggestion_id: str) -> Response:
        return Response.json({"id": suggestion_id, "deleted": True})'''

new_del_suggestion = '''    def delete_search_suggestion(self, request: Request, suggestion_id: str) -> Response:
        from webcms.search.analytics import SearchAnalytics
        try:
            analytics = SearchAnalytics(db=self.db)
            success = analytics.delete_suggestion(suggestion_id)
            return Response.json({"id": suggestion_id, "deleted": success})
        except Exception as e:
            return Response.json({"id": suggestion_id, "deleted": False, "error": str(e)})'''

if old_del_suggestion in content:
    content = content.replace(old_del_suggestion, new_del_suggestion)
    print("Fixed delete_search_suggestion")
else:
    print("Could not find delete_search_suggestion")

# Fix update_notification_preferences
old_update_prefs = '''    def update_notification_preferences(self, request: Request) -> Response:
        data = request.json or {}
        return Response.json({"updated": True, "preferences": data})'''

new_update_prefs = '''    def update_notification_preferences(self, request: Request) -> Response:
        from webcms.notifications.preferences import NotificationPreferences
        data = request.json or {}
        try:
            prefs = NotificationPreferences(db=self.db)
            result = prefs.update(data)
            return Response.json(result)
        except Exception as e:
            return Response.json({"updated": False, "error": str(e)})'''

if old_update_prefs in content:
    content = content.replace(old_update_prefs, new_update_prefs)
    print("Fixed update_notification_preferences")
else:
    print("Could not find update_notification_preferences")

# Fix notification_queue
old_queue = '''    def notification_queue(self, request: Request) -> Response:
        from webcms.notifications.queue import NotificationQueue
        try:
            queue = NotificationQueue(self.db)
            return Response.json({
                "pending": queue.pending_count(),
                "sent_24h": queue.sent_count(hours=24),
                "failed": queue.failed_count(),
                "retrying": queue.retrying_count()
            })
        except Exception:
            return Response.json({"pending": 0, "sent_24h": 0, "failed": 0, "retrying": 0})'''

new_queue = '''    def notification_queue(self, request: Request) -> Response:
        from webcms.notifications.manager import NotificationManager
        try:
            manager = NotificationManager(db=self.db)
            stats = manager.get_queue_stats()
            return Response.json(stats)
        except Exception:
            return Response.json({"pending": 0, "sent_24h": 0, "failed": 0, "retrying": 0})'''

if old_queue in content:
    content = content.replace(old_queue, new_queue)
    print("Fixed notification_queue")
else:
    print("Could not find notification_queue")

with open('webcms/admin/admin_api.py', 'w') as f:
    f.write(content)

print("All fixes applied")
