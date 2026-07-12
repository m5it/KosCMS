"""
Notification API endpoints.
"""

from webcms.core.request import Request
from webcms.core.response import Response
from .manager import NotificationManager


class NotificationAPI:
    """Notification API."""

    def __init__(self, notification_manager=None):
        self.manager = notification_manager or NotificationManager()

    async def get_notifications(self, request: Request, user_id: str):
        """Get in-app notifications for user."""
        unread_only = request.get_param("unread", "false").lower() == "true"
        limit = int(request.get_param("limit", "50"))
        notifications = self.manager.get_in_app_notifications(
            user_id, unread_only=unread_only, limit=limit
        )
        return Response.json({
            "notifications": notifications,
            "unread_count": len([n for n in notifications if not n["read"]])
        })

    async def mark_read(self, request: Request, notification_id: int):
        """Mark notification as read."""
        success = self.manager.mark_read(notification_id)
        return Response.json({"marked_read": success})

    async def get_preferences(self, request: Request, user_id: str):
        """Get notification preferences."""
        prefs = self.manager.preferences.get_preferences(user_id)
        return Response.json({"preferences": prefs})

    async def update_preferences(self, request: Request, user_id: str):
        """Update notification preferences."""
        data = request.json or {}
        prefs = self.manager.preferences.update_preferences(user_id, data)
        return Response.json({"preferences": prefs})

    async def send_notification(self, request: Request):
        """Send notification manually."""
        data = request.json or {}
        required = ["user_id", "event_type", "subject", "context"]
        for field in required:
            if field not in data:
                return Response.error(f"Missing {field}", 400)

        result = await self.manager.notify(
            user_id=data["user_id"],
            event_type=data["event_type"],
            subject=data["subject"],
            context=data["context"],
            channels=data.get("channels", ["email", "in_app"])
        )
        return Response.json(result)

    async def send_digest(self, request: Request):
        """Trigger digest emails."""
        data = request.json or {}
        digest_type = data.get("digest_type", "daily")
        result = await self.manager.send_digest(digest_type)
        return Response.json(result)

    async def process_queue(self, request: Request):
        """Process email queue."""
        result = await self.manager.process_email_queue()
        return Response.json(result)

    async def queue_stats(self, request: Request):
        """Get email queue stats."""
        return Response.json(self.manager.email_queue.get_stats())


def register_notification_api(app, notification_manager=None):
    """Register notification API routes."""
    api = NotificationAPI(notification_manager)

    @app.route("/api/v1/notifications/<user_id>", methods=["GET"])
    def get_notifications(request, user_id):
        return api.get_notifications(request, user_id)

    @app.route("/api/v1/notifications/<notification_id>/read", methods=["POST"])
    def mark_read(request, notification_id):
        return api.mark_read(request, int(notification_id))

    @app.route("/api/v1/notifications/<user_id>/preferences", methods=["GET"])
    def get_preferences(request, user_id):
        return api.get_preferences(request, user_id)

    @app.route("/api/v1/notifications/<user_id>/preferences", methods=["PUT"])
    def update_preferences(request, user_id):
        return api.update_preferences(request, user_id)

    @app.route("/api/v1/notifications/send", methods=["POST"])
    def send_notification(request):
        return api.send_notification(request)

    @app.route("/api/v1/notifications/digest", methods=["POST"])
    def send_digest(request):
        return api.send_digest(request)

    @app.route("/api/v1/notifications/queue/process", methods=["POST"])
    def process_queue(request):
        return api.process_queue(request)

    @app.route("/api/v1/notifications/queue/stats", methods=["GET"])
    def queue_stats(request):
        return api.queue_stats(request)
