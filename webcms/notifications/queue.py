"""
Email queue with retry logic.
"""

from datetime import datetime, timedelta
from typing import List, Dict


class EmailQueue:
    """Queue for outgoing emails with retries."""

    def __init__(self, max_retries=3, retry_delays=None):
        self._queue: List[Dict] = []
        self._sent: List[Dict] = []
        self._failed: List[Dict] = []
        self.max_retries = max_retries
        self.retry_delays = retry_delays or [60, 300, 900]

    def enqueue(self, to_email, subject, html_body, text_body=None,
                from_email=None, metadata=None):
        """Add email to queue."""
        item = {
            "id": len(self._queue) + 1,
            "to_email": to_email,
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body,
            "from_email": from_email,
            "metadata": metadata or {},
            "attempts": 0,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        self._queue.append(item)
        return item

    async def process(self, adapter):
        """Process all queued emails."""
        pending = [item for item in self._queue if item["status"] == "pending"]
        for item in pending:
            result = await adapter.send(
                item["to_email"],
                item["subject"],
                item["html_body"],
                item["text_body"],
                item["from_email"]
            )
            if result.get("success"):
                item["status"] = "sent"
                item["sent_at"] = datetime.utcnow().isoformat()
                self._sent.append(item)
            else:
                item["attempts"] += 1
                if item["attempts"] >= self.max_retries:
                    item["status"] = "failed"
                    item["error"] = result.get("error")
                    self._failed.append(item)
        return {"sent": len(self._sent), "failed": len(self._failed)}

    async def retry_failed(self, adapter):
        """Retry failed emails."""
        for item in self._failed:
            item["status"] = "pending"
            item["attempts"] = 0
        self._failed = []
        return await self.process(adapter)

    def get_stats(self) -> Dict:
        """Get queue statistics."""
        return {
            "pending": len([i for i in self._queue if i["status"] == "pending"]),
            "sent": len(self._sent),
            "failed": len(self._failed),
            "total": len(self._queue)
        }


class NotificationQueue:
    """Notification queue manager for admin API.
    
    Provides a unified interface for notification queue statistics
    that works with both SQLAlchemy and KosDB backends.
    """
    
    def __init__(self, db=None):
        self.db = db
        self._email_queue = EmailQueue()
    
    def pending_count(self) -> int:
        """Get count of pending notifications."""
        if self.db is None:
            return len([i for i in self._email_queue._queue if i.get("status") == "pending"])
        # For KosDB or SQLAlchemy, query the notifications table/collection
        try:
            if hasattr(self.db, 'query'):
                # SQLAlchemy backend
                from webcms.models.system import Notification
                return self.db.query(Notification).filter_by(status='pending').count()
            else:
                # KosDB backend - assume dict-like interface with notification keys
                notifications = self.db.get('notifications', [])
                return len([n for n in notifications if n.get('status') == 'pending'])
        except Exception:
            return 0
    
    def sent_count(self, hours: int = 24) -> int:
        """Get count of notifications sent in the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        if self.db is None:
            return len([
                i for i in self._email_queue._sent 
                if i.get('sent_at') and datetime.fromisoformat(i['sent_at']) > cutoff
            ])
        
        try:
            if hasattr(self.db, 'query'):
                from webcms.models.system import Notification
                return self.db.query(Notification).filter(
                    Notification.status == 'sent',
                    Notification.sent_at > cutoff
                ).count()
            else:
                notifications = self.db.get('notifications', [])
                return len([
                    n for n in notifications 
                    if n.get('status') == 'sent' and n.get('sent_at') and 
                       datetime.fromisoformat(n['sent_at']) > cutoff
                ])
        except Exception:
            return 0
    
    def failed_count(self) -> int:
        """Get count of failed notifications."""
        if self.db is None:
            return len(self._email_queue._failed)
        
        try:
            if hasattr(self.db, 'query'):
                from webcms.models.system import Notification
                return self.db.query(Notification).filter_by(status='failed').count()
            else:
                notifications = self.db.get('notifications', [])
                return len([n for n in notifications if n.get('status') == 'failed'])
        except Exception:
            return 0
    
    def retrying_count(self) -> int:
        """Get count of notifications currently retrying."""
        if self.db is None:
            return len([
                i for i in self._email_queue._queue 
                if i.get('status') == 'pending' and i.get('attempts', 0) > 0
            ])
        
        try:
            if hasattr(self.db, 'query'):
                from webcms.models.system import Notification
                return self.db.query(Notification).filter(
                    Notification.status == 'pending',
                    Notification.attempts > 0
                ).count()
            else:
                notifications = self.db.get('notifications', [])
                return len([
                    n for n in notifications 
                    if n.get('status') == 'pending' and n.get('attempts', 0) > 0
                ])
        except Exception:
            return 0
