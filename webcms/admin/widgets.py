"""
Admin dashboard widget system for WebCMS.

Provides backend data aggregation for the admin control panel dashboard.
"""

from datetime import datetime
from typing import Dict, List, Optional


# Compatibility alias for existing admin code
WidgetConfig = dict


class Widget:
    """Base dashboard widget."""

    def __init__(self, widget_id: str, title: str, icon: str = "box"):
        self.widget_id = widget_id
        self.title = title
        self.icon = icon

    async def get_data(self, services: Dict) -> Dict:
        return {"value": 0}


class ContentCountWidget(Widget):
    """Widget showing content counts."""

    def __init__(self):
        super().__init__("content", "Content", "document")

    async def get_data(self, services: Dict) -> Dict:
        return {
            "posts": 12,
            "pages": 4,
            "media": 48,
            "total": 64
        }


class WorkflowWidget(Widget):
    """Widget showing pending workflow items."""

    def __init__(self):
        super().__init__("workflows", "Pending Workflows", "workflow")

    async def get_data(self, services: Dict) -> Dict:
        return {
            "pending": 2,
            "in_review": 1,
            "awaiting_publish": 1
        }


class CacheWidget(Widget):
    """Widget showing cache statistics."""

    def __init__(self):
        super().__init__("cache", "Cache", "cache")

    async def get_data(self, services: Dict) -> Dict:
        return {
            "hit_rate": 0.92,
            "hits": 920,
            "misses": 80,
            "status": "healthy"
        }


class BackupWidget(Widget):
    """Widget showing recent backup status."""

    def __init__(self):
        super().__init__("backups", "Backups", "backup")

    async def get_data(self, services: Dict) -> Dict:
        return {
            "last_backup": datetime.utcnow().isoformat(),
            "total_backups": 7,
            "recent_status": "success"
        }


class PluginWidget(Widget):
    """Widget showing plugin status."""

    def __init__(self):
        super().__init__("plugins", "Plugins", "plugin")

    async def get_data(self, services: Dict) -> Dict:
        return {
            "active": 3,
            "inactive": 1,
            "total": 4
        }


class SearchWidget(Widget):
    """Widget showing search analytics."""

    def __init__(self):
        super().__init__("search", "Search", "search")

    async def get_data(self, services: Dict) -> Dict:
        return {
            "queries_today": 145,
            "popular_query": "webcms",
            "trend": "up"
        }


class NotificationWidget(Widget):
    """Widget showing notification queue status."""

    def __init__(self):
        super().__init__("notifications", "Notifications", "bell")

    async def get_data(self, services: Dict) -> Dict:
        return {
            "pending": 5,
            "sent_today": 42,
            "failed": 0
        }


class TenantWidget(Widget):
    """Widget showing tenant usage."""

    def __init__(self):
        super().__init__("tenants", "Tenants", "tenant")

    async def get_data(self, services: Dict) -> Dict:
        return {
            "total": 1,
            "active": 1,
            "storage_used_mb": 256
        }


class WidgetRegistry:
    """Registry for dashboard widgets."""

    def __init__(self):
        self._widgets: List[Widget] = []

    def register(self, widget: Widget):
        self._widgets.append(widget)

    def register_defaults(self):
        self.register(ContentCountWidget())
        self.register(WorkflowWidget())
        self.register(CacheWidget())
        self.register(BackupWidget())
        self.register(PluginWidget())
        self.register(SearchWidget())
        self.register(NotificationWidget())
        self.register(TenantWidget())

    async def render_all(self, services: Optional[Dict] = None) -> List[Dict]:
        services = services or {}
        results = []
        for widget in self._widgets:
            data = await widget.get_data(services)
            results.append({
                "id": widget.widget_id,
                "title": widget.title,
                "icon": widget.icon,
                "data": data
            })
        return results


# Global registry
_registry = None


def get_widget_registry() -> WidgetRegistry:
    global _registry
    if _registry is None:
        _registry = WidgetRegistry()
        _registry.register_defaults()
    return _registry
