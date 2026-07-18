"""
Notification manager combining email, in-app, and push notifications with KosDB.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from .templates import TemplateEngine
from .preferences import NotificationPreferences
from .queue import EmailQueue, NotificationQueue


class NotificationManager:
    """Central notification manager with KosDB persistence."""

    def __init__(self, db=None, email_adapter=None, preferences=None, template_engine=None):
        self.db = db
        self.email_adapter = email_adapter
        self.preferences = preferences or NotificationPreferences(db=db)
        self.templates = template_engine or TemplateEngine()
        self.templates.register_defaults()
        self.email_queue = EmailQueue()
        self._in_app: List[Dict] = []
        self._push_handlers: List = []
        self._ensure_tables()
        self._load_from_kosdb()

    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods

    def _ensure_tables(self):
        """Ensure notification tables exist."""
        if not self.db or not self._is_kosdb():
            return

        try:
            tables = self.db.list_tables()
        except Exception:
            tables = []

        # In-app notifications table
        if 'in_app_notifications' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE in_app_notifications (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        event_type TEXT,
                        subject TEXT,
                        context TEXT,
                        is_read TEXT DEFAULT '0',
                        created_at TEXT
                    )
                """)
            except Exception:
                pass

        # Notification queue table
        if 'notification_queue' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE notification_queue (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        to_email TEXT,
                        subject TEXT,
                        html_body TEXT,
                        text_body TEXT,
                        status TEXT DEFAULT 'pending',
                        attempts INTEGER DEFAULT 0,
                        created_at TEXT,
                        sent_at TEXT,
                        error TEXT
                    )
                """)
            except Exception:
                pass

    def _load_from_kosdb(self):
        """Load notifications from KosDB."""
        if not self.db or not self._is_kosdb():
            return

        try:
            result = self.db.query("SELECT * FROM in_app_notifications WHERE is_read='0'")
            for row in result.get('rows', []):
                self._in_app.append({
                    "id": row['id'],
                    "user_id": row['user_id'],
                    "event_type": row['event_type'],
                    "subject": row['subject'],
                    "context": json.loads(row['context']) if row.get('context') else {},
                    "read": row.get('is_read') == '1',
                    "created_at": row['created_at']
                })
        except Exception:
            pass

    def _save_in_app_to_kosdb(self, notification: Dict):
        """Save in-app notification to KosDB."""
        if not self.db or not self._is_kosdb():
            return

        try:
            import uuid
            notif_id = str(uuid.uuid4())
            context = json.dumps(notification.get('context', {}))
            now = datetime.utcnow().isoformat()
            
            self.db.execute(f"""
                INSERT INTO in_app_notifications 
                (id, user_id, event_type, subject, context, is_read, created_at)
                VALUES (
                    '{notif_id}',
                    '{notification.get('user_id', '')}',
                    '{notification.get('event_type', '')}',
                    '{notification.get('subject', '')}',
                    '{context}',
                    '{1 if notification.get('read') else 0}',
                    '{now}'
                )
            """)
            notification['id'] = notif_id
        except Exception:
            pass

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
                notif = {
                    "user_id": user_id,
                    "event_type": event_type,
                    "subject": subject,
                    "context": context,
                    "read": False,
                    "created_at": datetime.utcnow().isoformat()
                }
                self._in_app.append(notif)
                self._save_in_app_to_kosdb(notif)
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

    def mark_read(self, notification_id: str) -> bool:
        """Mark in-app notification as read."""
        for notif in self._in_app:
            if notif.get('id') == notification_id:
                notif["read"] = True
                # Update in KosDB
                if self.db and self._is_kosdb():
                    try:
                        self.db.execute(f"UPDATE in_app_notifications SET is_read='1' WHERE id='{notification_id}'")
                    except Exception:
                        pass
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

    # ============ Sync Methods for Admin API ============

    def send_bulk(self, recipients: List[str], subject: str, body: str) -> int:
        """Send bulk notifications (sync version)."""
        count = 0
        for recipient in recipients:
            # Queue email
            self.email_queue.enqueue(
                to_email=recipient,
                subject=subject,
                html_body=body,
                metadata={"bulk": True}
            )
            count += 1
        return count

    def trigger_digest(self, digest_type: str = "daily") -> int:
        """Trigger digest generation (sync version)."""
        user_ids = self.preferences.get_digest_users(digest_type)
        return len(user_ids)

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get notification queue statistics."""
        queue = NotificationQueue(db=self.db)
        return {
            "pending": queue.pending_count(),
            "sent_24h": queue.sent_count(hours=24),
            "failed": queue.failed_count(),
            "retrying": queue.retrying_count()
        }
