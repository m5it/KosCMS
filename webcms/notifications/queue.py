"""
Email queue with retry logic.
"""

from datetime import datetime
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
