"""
Backup monitoring and alerts.
"""

from datetime import datetime
from typing import Dict, List


class BackupMonitor:
    """Monitors backup health and triggers alerts."""

    def __init__(self):
        self._alerts: List[Dict] = []
        self._history: List[Dict] = []
        self._alert_handlers: List = []

    def record_backup(self, backup_id: str, status: str, details: Dict = None):
        """Record backup attempt."""
        entry = {
            "backup_id": backup_id,
            "status": status,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        self._history.append(entry)

        if status == "failed":
            self._trigger_alert("backup_failed", entry)

    def _trigger_alert(self, alert_type: str, data: Dict):
        """Trigger alert handlers."""
        alert = {
            "type": alert_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._alerts.append(alert)
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"Alert handler error: {e}")

    def register_alert_handler(self, handler):
        """Register alert handler."""
        self._alert_handlers.append(handler)

    def get_status(self) -> Dict:
        """Get backup monitoring status."""
        recent = self._history[-10:]
        failed = [h for h in self._history if h["status"] == "failed"]
        return {
            "total_backups": len(self._history),
            "failed_backups": len(failed),
            "recent_history": recent,
            "alerts": self._alerts[-10:],
            "healthy": len(failed) == 0 or len(failed) < len(self._history) * 0.1
        }
