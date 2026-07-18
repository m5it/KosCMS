#!/usr/bin/env python3
# Test /api/v1/admin/pages and /api/v1/admin/posts with KosDB and SQLAlchemy serialization.

import importlib.util
import json
from datetime import datetime
from unittest.mock import MagicMock

spec = importlib.util.spec_from_file_location("admin_api", "webcms/admin/admin_api.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
AdminAPI = mod.AdminAPI
from webcms.core.request import Request


def test_sqlalchemy_serialization():
    api = AdminAPI(db=None)

    page = MagicMock()
    page.id = "page-1"
    page.title = "About Us"
    page.slug = "about-us"
    page.status = "published"
    page.updated_at = datetime(2026, 7, 18, 10, 0, 0)

    author = MagicMock()
    author.display_name = "Admin"
    page.author = author

    serialized = api._serialize_page(page)
    assert serialized["id"] == "page-1"
    assert serialized["title"] == "About Us"
    assert serialized["author"] == "Admin"
    assert serialized["updated_at"] == "2026-07-18T10:00:00"

    post = MagicMock()
    post.id = "post-1"
    post.title = "Hello World"
    post.slug = "hello-world"
    post.status = "draft"
    post.updated_at = None
    post.author = None
    post.author_id = None

    serialized = api._serialize_post(post)
    assert serialized["id"] == "post-1"
    assert serialized["title"] == "Hello World"
    assert serialized["author"] is None
    assert serialized["updated_at"] is None

    print("SQLAlchemy serialization: OK")


class FakeKosDB:
    def __init__(self):
        self.tables = {}
        self._class_name = "FakeKosDBClient"

    def list_tables(self):
        return list(self.tables.keys())

    def execute(self, command):
        cmd = command.strip()
        up = cmd.upper()
        if up.startswith("CREATE TABLE"):
            name = cmd.split()[2]
            self.tables[name] = []
            return "OK"
        if up.startswith("INSERT INTO"):
            parts = cmd.split(" VALUES ", 1)
            table = parts[0].split()[2]
            cols = parts[0].split("(", 1)[1].rstrip(")").split(", ")
            vals = parts[1].strip("()").split(", ")
            record = {}
            for c, v in zip(cols, vals):
                if v == "NULL":
                    record[c] = None
                else:
                    record[c] = v.strip("'")
            self.tables[table].append(record)
            return "OK"
        if up.startswith("UPDATE"):
            table = cmd.split()[1]
            rest = cmd.split(" SET ", 1)[1]
            set_part = rest.split(" WHERE ", 1)[0]
            where_part = rest.split(" WHERE ", 1)[1] if " WHERE " in rest else ""
            sets = {}
            for item in set_part.split(", "):
                k, v = item.split("=", 1)
                sets[k] = None if v == "NULL" else v.strip("'")
            for row in self.tables.get(table, []):
                if not where_part or self._match(row, where_part):
                    row.update(sets)
            return "OK"
        if up.startswith("SELECT"):
            table = cmd.split(" FROM ", 1)[1].split()[0]
            rows = list(self.tables.get(table, []))
            if " WHERE " in cmd:
                where = cmd.split(" WHERE ", 1)[1]
                rows = [r for r in rows if self._match(r, where)]
            return self._format(rows)
        return "ERROR: unknown command"

    def query(self, command):
        resp = self.execute(command)
        if resp.startswith("ERROR"):
            return {"error": resp, "rows": []}
        lines = resp.split("\n")
        if len(lines) < 3:
            return {"rows": []}
        cols = [c.strip() for c in lines[1].split("|")[1:-1]]
        rows = []
        for line in lines[3:-1]:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if not any(cells):
                continue
            rows.append({cols[i]: cells[i] for i in range(len(cells))})
        return {"rows": rows}

    def _match(self, row, where):
        conditions = [c.strip().strip("()") for c in where.split(" AND ")]
        for cond in conditions:
            if " OR " in cond:
                sub = [s.strip().strip("()") for s in cond.split(" OR ")]
                if not any(self._eval(row, s) for s in sub):
                    return False
            elif not self._eval(row, cond):
                return False
        return True

    def _eval(self, row, cond):
        cond = cond.strip().strip("()")
        if "=" not in cond:
            return False
        key, val = cond.split("=", 1)
        key = key.strip()
        val = val.strip().strip("'")
        return str(row.get(key, "")) == val

    def _format(self, rows):
        if not rows:
            return "Empty set"
        cols = list(rows[0].keys())
        lines = ["+" + "+".join("-" * (len(c) + 2) for c in cols) + "+"]
        lines.append("|" + "|".join(f" {c} " for c in cols) + "|")
        lines.append(lines[0])
        for row in rows:
            lines.append("|" + "|".join(f" {str(row.get(c, ''))} " for c in cols) + "|")
        lines.append(lines[0])
        lines.append(f"{len(rows)} row(s) in set")
        return "\n".join(lines)


def test_kosdb():
    db = FakeKosDB()
    api = AdminAPI(db=db)

    req = Request({"REQUEST_METHOD": "POST", "CONTENT_TYPE": "application/json"})
    req._json = {
        "title": "Kos Page",
        "slug": "kos-page",
        "content": "Kos content",
        "status": "draft"
    }
    resp = api.create_page(req)
    assert resp.status == 201, resp.body
    page = json.loads(resp.body)
    assert page["title"] == "Kos Page"
    page_id = page["id"]

    req = Request({"REQUEST_METHOD": "GET"})
    resp = api.list_pages(req)
    data = json.loads(resp.body)
    assert len(data["pages"]) == 1
    assert data["pages"][0]["updated_at"] is not None

    req = Request({"REQUEST_METHOD": "PUT", "CONTENT_TYPE": "application/json"})
    req._json = {"title": "Kos Page Updated", "status": "published"}
    resp = api.update_page(req, page_id)
    assert resp.status == 200, resp.body
    updated = json.loads(resp.body)
    assert updated["title"] == "Kos Page Updated"

    req = Request({"REQUEST_METHOD": "POST", "CONTENT_TYPE": "application/json"})
    req._json = {
        "title": "Kos Post",
        "slug": "kos-post",
        "content": "Kos post content",
        "status": "draft"
    }
    resp = api.create_post(req)
    assert resp.status == 201, resp.body
    post = json.loads(resp.body)
    post_id = post["id"]

    req = Request({"REQUEST_METHOD": "GET"})
    resp = api.list_posts(req)
    data = json.loads(resp.body)
    assert len(data["posts"]) == 1

    req = Request({"REQUEST_METHOD": "PUT", "CONTENT_TYPE": "application/json"})
    req._json = {"title": "Kos Post Updated", "status": "published"}
    resp = api.update_post(req, post_id)
    assert resp.status == 200, resp.body
    updated = json.loads(resp.body)
    assert updated["title"] == "Kos Post Updated"

    req = Request({"REQUEST_METHOD": "DELETE"})
    resp = api.delete_page(req, page_id)
    assert resp.status == 200, resp.body

    resp = api.delete_post(req, post_id)
    assert resp.status == 200, resp.body

    req = Request({"REQUEST_METHOD": "GET"})
    resp = api.list_pages(req)
    assert len(json.loads(resp.body)["pages"]) == 0
    resp = api.list_posts(req)
    assert len(json.loads(resp.body)["posts"]) == 0

    print("KosDB path: OK")


if __name__ == "__main__":
    test_sqlalchemy_serialization()
    test_kosdb()
    print("All admin content tests passed.")
