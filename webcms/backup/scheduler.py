"""
Automated backup scheduler.
"""

import asyncio
from datetime import datetime
from typing import Callable, List


class BackupScheduler:
    """Schedules automated backups."""

    def __init__(self):
        self._tasks: List[dict] = []
        self._running = False

    def schedule(self, name: str, interval_hours: int, task: Callable):
        """Schedule recurring backup task."""
        self._tasks.append({
            "name": name,
            "interval_hours": interval_hours,
            "task": task,
            "last_run": None
        })

    async def run(self):
        """Run scheduler loop."""
        self._running = True
        while self._running:
            now = datetime.utcnow()
            for item in self._tasks:
                last_run = item["last_run"]
                interval = item["interval_hours"]
                if last_run is None or (now - last_run).total_seconds() >= interval * 3600:
                    try:
                        await item["task"]()
                        item["last_run"] = now
                    except Exception as e:
                        print(f"Backup task {item['name']} failed: {e}")
            await asyncio.sleep(60)

    def stop(self):
        """Stop scheduler."""
        self._running = False

    def get_schedule(self):
        """Get scheduled tasks."""
        return [
            {
                "name": t["name"],
                "interval_hours": t["interval_hours"],
                "last_run": t["last_run"].isoformat() if t["last_run"] else None
            }
            for t in self._tasks
        ]
