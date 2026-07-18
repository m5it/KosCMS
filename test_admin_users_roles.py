#!/usr/bin/env python3
# Test /api/v1/admin/users and /api/v1/admin/roles CRUD with KosDB.

import importlib.util
import json

spec = importlib.util.spec_from_file_location("admin_api", "webcms/admin/admin_api.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
AdminAPI = mod.AdminAPI
from webcms.core.request import Request


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
        if up.startswith("DELETE FROM"):
            table = cmd.split()[2]
            where_part = cmd.split(" WHERE ", 1)[1] if " WHERE " in cmd else ""
            rows = self.tables.get(table, [])
            kept = []
            for row in rows:
                if where_part and self._match(row, where_part):
                    continue
                kept.append(row)
            self.tables[table] = kept
            return "OK"
        if up.startswith("SELECT"):
            table = cmd.split(" FROM ", 1)[1].split()[0]
            rows = list(self.tables.get(table, []))
            if " WHERE " in cmd:
                where = cmd.split(" WHERE ", 1)[1]
                rows = [r for r in rows if self._match(r, where)]
            if " IN (" in cmd:
                # Simple IN clause parsing
                field = cmd.split(" WHERE ", 1)[1].split(" IN ")[0]
                vals_part = cmd.split(" IN ", 1)[1].strip().strip("()")
                vals = [v.strip().strip("'") for v in vals_part.split(",")]
                rows = [r for r in rows if str(r.get(field, "")) in vals]
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


def test_kosdb_users_roles():
    db = FakeKosDB()
    api = AdminAPI(db=db)

    # List roles seeds defaults
    req = Request({"REQUEST_METHOD": "GET"})
    resp = api.list_roles(req)
    assert resp.status == 200, resp.body
    roles = json.loads(resp.body)["roles"]
    assert len(roles) == 3
    admin_role = next(r for r in roles if r["name"] == "admin")
    assert "users:manage" in admin_role["permissions"]

    # Create a new role
    req = Request({"REQUEST_METHOD": "POST", "CONTENT_TYPE": "application/json"})
    req._json = {"name": "moderator", "description": "Moderator", "permissions": ["content:delete", "media:read"]}
    resp = api.create_role(req)
    assert resp.status == 201, resp.body
    mod = json.loads(resp.body)
    assert mod["name"] == "moderator"
    assert "content:delete" in mod["permissions"]

    # Update role
    req = Request({"REQUEST_METHOD": "PUT", "CONTENT_TYPE": "application/json"})
    req._json = {"description": "Updated", "permissions": ["content:delete"]}
    resp = api.update_role(req, mod["id"])
    assert resp.status == 200, resp.body
    updated = json.loads(resp.body)
    assert updated["description"] == "Updated"
    assert updated["permissions"] == ["content:delete"]

    # Create user with role
    req = Request({"REQUEST_METHOD": "POST", "CONTENT_TYPE": "application/json"})
    req._json = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret",
        "display_name": "Alice",
        "is_active": True,
        "role": "editor"
    }
    resp = api.create_user(req)
    assert resp.status == 201, resp.body
    user = json.loads(resp.body)
    assert user["username"] == "alice"
    assert user["role"] == "editor"

    # List users
    req = Request({"REQUEST_METHOD": "GET"})
    resp = api.list_users(req)
    assert resp.status == 200, resp.body
    users = json.loads(resp.body)["users"]
    assert len(users) == 1
    assert users[0]["role"] == "editor"
    assert users[0]["is_active"] is True

    # Update user role
    req = Request({"REQUEST_METHOD": "PUT", "CONTENT_TYPE": "application/json"})
    req._json = {"role": "admin", "is_active": False}
    resp = api.update_user(req, user["id"])
    assert resp.status == 200, resp.body
    updated = json.loads(resp.body)
    assert updated["role"] == "admin"
    assert updated["is_active"] is False

    # Delete user
    req = Request({"REQUEST_METHOD": "DELETE"})
    resp = api.delete_user(req, user["id"])
    assert resp.status == 200, resp.body

    # Delete role
    req = Request({"REQUEST_METHOD": "DELETE"})
    resp = api.delete_role(req, mod["id"])
    assert resp.status == 200, resp.body

    # Verify lists
    req = Request({"REQUEST_METHOD": "GET"})
    resp = api.list_users(req)
    assert len(json.loads(resp.body)["users"]) == 0
    resp = api.list_roles(req)
    assert len(json.loads(resp.body)["roles"]) == 3

    print("KosDB users/roles: OK")


if __name__ == "__main__":
    test_kosdb_users_roles()
    print("All users/roles tests passed.")
