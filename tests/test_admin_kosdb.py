#!/usr/bin/env python3
"""
Test admin API endpoints with a KosDB-backed application.

This script creates an in-memory WebCMS app using a mock KosDB client
and verifies that the admin endpoints return 200 responses without
calling SQLAlchemy methods on the KosDB client.
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class MockKosDBClient:
    """
    Minimal mock of KosDBClient that stores tables in memory and
    responds to SQL-like query()/execute() calls.
    """

    def __init__(self):
        self.tables = {
            "users": [
                {"id": "u1", "username": "alice", "email": "alice@example.com",
                 "display_name": "Alice", "is_active": 1, "is_deleted": 0,
                 "roles": [{"name": "admin"}]},
            ],
            "posts": [
                {"id": "p1", "title": "Hello", "slug": "hello", "status": "published",
                 "author": {"display_name": "Alice"}, "updated_at": "2026-07-18T10:00:00"},
            ],
            "pages": [
                {"id": "pg1", "title": "About", "slug": "about", "status": "published",
                 "author": {"display_name": "Alice"}, "updated_at": "2026-07-18T10:00:00"},
            ],
            "media": [
                {"id": "m1", "filename": "logo.png", "file_url": "/media/logo.png",
                 "mime_type": "image/png", "width": 100, "height": 100, "is_deleted": 0},
            ],
            "roles": [
                {"id": "r1", "name": "admin", "description": "Administrator",
                 "permissions": "users.manage,content.manage"},
            ],
            "settings": [
                {"key": "site_name", "value": "Test Site", "type": "str"},
            ],
        }

    def query(self, command: str):
        cmd = command.strip().upper()
        if cmd.startswith("SELECT COUNT"):
            table = self._extract_table(command)
            rows = self.tables.get(table, [])
            return {"rows": [{"COUNT": len(rows)}], "count": len(rows)}
        if cmd.startswith("SELECT * FROM"):
            table = self._extract_table(command)
            rows = list(self.tables.get(table, []))
            # Very naive WHERE/ORDER BY/LIMIT handling for testing
            lower = command.lower()
            if " where " in lower:
                # Simple equality filter parsing is not fully implemented;
                # return all rows for this mock.
                pass
            if " order by " in lower:
                # No sorting in mock
                pass
            if " limit " in lower:
                try:
                    limit = int(lower.split(" limit ")[-1].split()[0])
                    rows = rows[:limit]
                except ValueError:
                    pass
            return {"rows": rows, "count": len(rows)}
        return {"rows": [], "count": 0}

    def execute(self, command: str):
        cmd = command.strip().upper()
        if cmd.startswith("INSERT INTO"):
            table = self._extract_table(command)
            self.tables.setdefault(table, []).append({"id": str(uuid.uuid4())})
            return "OK 1 row(s) affected"
        if cmd.startswith("UPDATE"):
            table = self._extract_table(command)
            return "OK 1 row(s) affected"
        return "OK"

    @staticmethod
    def _extract_table(command: str) -> str:
        lower = command.lower()
        if " from " in lower:
            return lower.split(" from ")[1].split()[0].strip()
        if " into " in lower:
            return lower.split(" into ")[1].split()[0].strip()
        return ""


def run_tests():
    from webcms.app_factory import create_app
    from webcms.core.request import Request

    # Create app with mock KosDB client injected
    app = create_app()
    mock_db = MockKosDBClient()
    app.container.register("kosdb", mock_db)
    app.container.register("db", mock_db)

    api = app.container._services.get("admin_api")
    if api is None:
        # Find registered admin api instance
        from webcms.admin.admin_api import AdminAPI
        api = AdminAPI(db=mock_db)

    endpoints = [
        ("dashboard", api.dashboard, {}),
        ("list_pages", api.list_pages, {}),
        ("list_posts", api.list_posts, {}),
        ("list_users", api.list_users, {}),
        ("list_roles", api.list_roles, {}),
        ("list_media", api.list_media, {}),
        ("get_settings", api.get_settings, {}),
    ]

    dummy_request = Request({"REQUEST_METHOD": "GET", "PATH_INFO": "/"})
    failed = False

    for name, handler, kwargs in endpoints:
        try:
            response = handler(dummy_request, **kwargs)
            status = getattr(response, "status", 200)
            if status == 200:
                print(f"✅ {name}: OK ({status})")
            else:
                print(f"❌ {name}: status {status}")
                failed = True
        except Exception as exc:
            print(f"❌ {name}: exception {exc}")
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run_tests())
