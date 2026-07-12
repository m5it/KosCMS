"""
Notification manager combining email, in-app, and push notifications.
"""

from datetime import datetime
from typing import Dict, List, Optional
from .templates import TemplateEngine
from .preferences import NotificationPreferences
from .queue import EmailQueue


class NotificationManager:
    """Central notification manager."""

    def __init__(self, email_adapter=None, preferences=None, template_engine=None):
        self.email_adapter = email_adapter
        self.preferences = preferences or NotificationPreferences()
        self.templates = template_engine or TemplateEngine()
        self.templates.register_defaults()
        self.email_queue = EmailQueue()
        self._in_app: List[Dict] = []
        self._push_handlers: List = []

    async def notify(self, user_id: str, event_type: str, subject: str,
                     context: Dict, channels: Optional[List[str]] = None):
        """Send notification to user across channels."""
        channels = channels or ["email", "in_app"]
        results = {}

        for channel in channels:
            if not self.preferences.is_enabled(user_id, channel, event_type):
                continue

            if channel == "email" and self.email_adapter:
                html = self.templates.render(event_type, context)
                self.email_queue.enqueue(
                    to_email=context.get("email"),
                    subject=subject,
                    html_body=html,
                    text_body=context.get("text_body"),
                    metadata={"user_id": user_id, "event_type": event_type}
                )
                results["email"] = "queued"

            elif channel == "in_app":
                self._in_app.append({
                    "user_id": user_id,
                    "event_type": event_type,
                    "subject": subject,
                    "context": context,
                    "read": False,
                    "created_at": datetime.utcnow().isoformat()
                })
                results["in_app"] = "created"

            elif channel == "push":
                for handler in self._push_handlers:
                    try:
                        await handler(user_id, event_type, subject, context)
                    except Exception as e:
                        print(f"Push handler error: {e}")
                results["push"] = "dispatched"

        return results

    async def send_digest(self, digest_type: str = "daily"):
        """Send digest emails to subscribed users."""
        user_ids = self.preferences.get_digest_users(digest_type)
        for user_id in user_ids:
            html = self.templates.render("daily_digest", {
                "pending_reviews": 2,
                "new_comments": 5,
                "published_posts": 3
            })
            self.email_queue.enqueue(
                to_email=f"{user_id}@example.com",
                subject=f"Your {digest_type} digest",
                html_body=html,
                metadata={"user_id": user_id, "digest_type": digest_type}
            )
        return {"queued": len(user_ids)}

    def get_in_app_notifications(self, user_id: str, unread_only: bool = False,
                                 limit: int = 50) -> List[Dict]:
        """Get in-app notifications for user."""
        notifications = [n for n in self._in_app if n["user_id"] == user_id]
        if unread_only:
            notifications = [n for n in notifications if not n["read"]]
        return sorted(notifications, key=lambda x: x["created_at"], reverse=True)[:limit]

    def mark_read(self, notification_id: int):
        """Mark in-app notification as read."""
        if 0 <= notification_id < len(self._in_app):
            self._in_app[notification_id]["read"] = True
            return True
        return False

    def register_push_handler(self, handler):
        """Register push notification handler."""
        self._push_handlers.append(handler)

    async def process_email_queue(self):
        """Process queued emails."""
        if not self.email_adapter:
            return {"error": "No email adapter configured"}
        return await self.email_queue.process(self.email_adapter)
