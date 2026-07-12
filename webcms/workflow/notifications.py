"""
Notification system for workflow events.
"""

import logging
from typing import Dict, List, Optional, Callable

logger = logging.getLogger("webcms.workflow.notifications")


class NotificationManager:
    """Manages workflow notifications."""

    def __init__(self):
        self._handlers: List[Callable] = []
        self._in_app_notifications: List[Dict] = []

    def register_handler(self, handler: Callable):
        """Register notification handler."""
        self._handlers.append(handler)

    async def notify(self, event_type: str, recipients: List[str],
                     title: str, message: str, data: Optional[Dict] = None):
        """Send notification to recipients."""
        notification = {
            "event_type": event_type,
            "recipients": recipients,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat() if 'datetime' in globals() else None
        }

        # Store in-app notification
        self._in_app_notifications.append(notification)

        # Call external handlers
        for handler in self._handlers:
            try:
                await handler(notification)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")

    async def notify_state_change(self, content_id, content_type,
                                  from_state, to_state, recipients,
                                  user_name="System"):
        """Notify about workflow state change."""
        await self.notify(
            event_type="workflow_state_change",
            recipients=recipients,
            title=f"Workflow state changed: {content_type}",
            message=f"{user_name} moved {content_type} {content_id} from {from_state} to {to_state}",
            data={
                "content_id": content_id,
                "content_type": content_type,
                "from_state": from_state,
                "to_state": to_state,
                "user_name": user_name
            }
        )

    async def notify_review_request(self, content_id, content_type,
                                    reviewer_id, reviewer_name, requester_name):
        """Notify reviewer about pending review."""
        await self.notify(
            event_type="review_request",
            recipients=[reviewer_id],
            title=f"Review requested: {content_type}",
            message=f"{requester_name} requested your review for {content_type} {content_id}",
            data={
                "content_id": content_id,
                "content_type": content_type,
                "reviewer": reviewer_name
            }
        )

    async def notify_scheduled_publish(self, content_id, content_type,
                                       publish_time, recipients):
        """Notify about scheduled publishing."""
        await self.notify(
            event_type="scheduled_publish",
            recipients=recipients,
            title=f"Scheduled publish: {content_type}",
            message=f"{content_type} {content_id} will be published at {publish_time}",
            data={
                "content_id": content_id,
                "content_type": content_type,
                "publish_time": publish_time
            }
        )

    def get_notifications(self, recipient=None, limit=50):
        """Get in-app notifications."""
        if recipient:
            return [
                n for n in self._in_app_notifications
                if recipient in n["recipients"]
            ][:limit]
        return self._in_app_notifications[-limit:]
