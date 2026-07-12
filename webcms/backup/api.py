"""
Backup API endpoints.
"""

from webcms.core.request import Request
from webcms.core.response import Response
from .engine import BackupEngine
from .restore import RestoreManager
from .scheduler import BackupScheduler
from .monitor import BackupMonitor


class BackupAPI:
    """Backup management API."""

    def __init__(self, backup_engine=None, restore_manager=None,
                 scheduler=None, monitor=None):
        self.engine = backup_engine or BackupEngine()
        self.restore = restore_manager or RestoreManager()
        self.scheduler = scheduler or BackupScheduler()
        self.monitor = monitor or BackupMonitor()

    async def list_backups(self, request: Request):
        """List all backups."""
        return Response.json({"backups": self.engine.list_backups()})

    async def create_backup(self, request: Request):
        """Trigger full backup."""
        data = request.json or {}
        backup_type = data.get("type", "full")
        try:
            result = await self.engine.backup_database(None, backup_type=backup_type)
            self.monitor.record_backup(result["backup_id"], "success", result)
            return Response.json(result, 201)
        except Exception as e:
            self.monitor.record_backup("manual", "failed", {"error": str(e)})
            return Response.error(str(e), 500)

    async def incremental_backup(self, request: Request):
        """Trigger incremental backup."""
        data = request.json or {}
        try:
            result = await self.engine.incremental_backup(None, data.get("changed_files", []))
            self.monitor.record_backup(result["database"]["backup_id"], "success", result)
            return Response.json(result, 201)
        except Exception as e:
            return Response.error(str(e), 500)

    async def restore_backup(self, request: Request, backup_id: str):
        """Restore backup by ID."""
        try:
            result = await self.restore.one_click_restore(backup_id, None)
            return Response.json(result)
        except Exception as e:
            return Response.error(str(e), 500)

    async def verify_backup(self, request: Request, backup_id: str):
        """Verify backup."""
        backup = self.engine.get_backup(backup_id)
        if not backup:
            return Response.not_found()
        result = await self.restore.verify_backup(backup_id, backup)
        return Response.json(result)

    async def get_schedule(self, request: Request):
        """Get backup schedule."""
        return Response.json({"schedule": self.scheduler.get_schedule()})

    async def add_schedule(self, request: Request):
        """Add scheduled backup task."""
        data = request.json or {}
        name = data.get("name")
        interval = data.get("interval_hours", 24)
        if not name:
            return Response.error("name required", 400)

        async def task():
            await self.engine.backup_database(None, backup_type="incremental")

        self.scheduler.schedule(name, interval, task)
        return Response.json({"scheduled": True})

    async def get_monitor_status(self, request: Request):
        """Get backup monitoring status."""
        return Response.json(self.monitor.get_status())


def register_backup_api(app, backup_api=None):
    """Register backup API routes."""
    api = backup_api or BackupAPI()

    @app.route("/api/v1/backups", methods=["GET"])
    def list_backups(request):
        return api.list_backups(request)

    @app.route("/api/v1/backups", methods=["POST"])
    def create_backup(request):
        return api.create_backup(request)

    @app.route("/api/v1/backups/incremental", methods=["POST"])
    def incremental_backup(request):
        return api.incremental_backup(request)

    @app.route("/api/v1/backups/<backup_id>/restore", methods=["POST"])
    def restore_backup(request, backup_id):
        return api.restore_backup(request, backup_id)

    @app.route("/api/v1/backups/<backup_id>/verify", methods=["POST"])
    def verify_backup(request, backup_id):
        return api.verify_backup(request, backup_id)

    @app.route("/api/v1/backups/schedule", methods=["GET"])
    def get_schedule(request):
        return api.get_schedule(request)

    @app.route("/api/v1/backups/schedule", methods=["POST"])
    def add_schedule(request):
        return api.add_schedule(request)

    @app.route("/api/v1/backups/monitor", methods=["GET"])
    def get_monitor_status(request):
        return api.get_monitor_status(request)
