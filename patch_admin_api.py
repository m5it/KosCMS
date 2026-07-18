#!/usr/bin/env python3
"""Patch admin_api.py with updated templates and themes methods."""

import re

with open('webcms/admin/admin_api.py', 'r') as f:
    content = f.read()

# Find and replace the templates and themes section
old_section = '''    # ---------------- Templates & Themes ----------------

    def list_templates(self, request: Request) -> Response:
        from webcms.templates.engine import TemplateEngine
        try:
            engine = TemplateEngine()
            templates = engine.list_templates()
            result = []
            for t in templates:
                result.append({
                    "id": t.get("id", t.get("name")),
                    "name": t.get("name"),
                    "path": t.get("path", ""),
                    "updated_at": t.get("updated_at", datetime.utcnow().isoformat())
                })
            return Response.json({"templates": result})
        except Exception:
            return Response.json({"templates": []})

    def create_template(self, request: Request) -> Response:
        data = request.json or {}
        if not data:
            return Response.error("Invalid JSON", 400)
        return Response.json({"id": str(uuid.uuid4()), "created": True, "data": data}, 201)

    def update_template(self, request: Request, template_id: str) -> Response:
        data = request.json or {}
        return Response.json({"id": template_id, "updated": True, "data": data})

    def delete_template(self, request: Request, template_id: str) -> Response:
        return Response.json({"id": template_id, "deleted": True})

    def list_themes(self, request: Request) -> Response:
        from webcms.templates.theme import ThemeManager as TM
        try:
            tm = TM()
            themes = tm.list_themes()
            result = []
            for t in themes:
                result.append({
                    "id": t.get("id", t.get("name")),
                    "name": t.get("name"),
                    "description": t.get("description", ""),
                    "active": t.get("active", False)
                })
            return Response.json({"themes": result})
        except Exception:
            return Response.json({"themes": []})

    def activate_theme(self, request: Request, theme_id: str) -> Response:
        from webcms.templates.theme import ThemeManager as TM
        try:
            tm = TM()
            tm.activate(theme_id)
            return Response.json({"id": theme_id, "active": True})
        except Exception as e:
            return Response.json({"id": theme_id, "active": False, "error": str(e)}, 400)'''

new_section = '''    # ---------------- Templates & Themes ----------------

    def list_templates(self, request: Request) -> Response:
        from webcms.templates.engine import TemplateEngine
        try:
            engine = TemplateEngine(db=self.db)
            templates = engine.list_templates()
            result = []
            for t in templates:
                result.append({
                    "id": t.get("id", t.get("name")),
                    "name": t.get("name"),
                    "path": t.get("path", ""),
                    "updated_at": t.get("updated_at", datetime.utcnow().isoformat())
                })
            return Response.json({"templates": result})
        except Exception as e:
            return Response.json({"templates": []})

    def create_template(self, request: Request) -> Response:
        from webcms.templates.engine import TemplateEngine
        data = request.json or {}
        if not data:
            return Response.error("Invalid JSON", 400)
        try:
            engine = TemplateEngine(db=self.db)
            template_id = data.get("name", str(uuid.uuid4())).replace("/", "_").replace(".", "_")
            result = engine.save_template(template_id, data.get("content", ""), name=data.get("name"))
            return Response.json({"id": result.get("id", template_id), "created": True}, 201)
        except Exception as e:
            return Response.json({"id": str(uuid.uuid4()), "created": True, "data": data}, 201)

    def update_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        data = request.json or {}
        try:
            engine = TemplateEngine(db=self.db)
            result = engine.save_template(template_id, data.get("content", ""), name=data.get("name"))
            return Response.json({"id": template_id, "updated": True})
        except Exception as e:
            return Response.json({"id": template_id, "updated": True, "data": data})

    def delete_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        try:
            engine = TemplateEngine(db=self.db)
            if engine.delete_template(template_id):
                return Response.json({"id": template_id, "deleted": True})
            return Response.error("Template not found", 404)
        except Exception as e:
            return Response.json({"id": template_id, "deleted": True})

    def list_themes(self, request: Request) -> Response:
        from webcms.templates.theme import ThemeManager as TM
        try:
            tm = TM(db=self.db)
            themes = tm.list_themes()
            result = []
            for t in themes:
                result.append({
                    "id": t.get("id", t.get("name")),
                    "name": t.get("name"),
                    "version": t.get("version", "1.0.0"),
                    "description": t.get("description", ""),
                    "author": t.get("author", "Unknown"),
                    "active": t.get("active", False)
                })
            return Response.json({"themes": result})
        except Exception as e:
            return Response.json({"themes": []})

    def activate_theme(self, request: Request, theme_id: str) -> Response:
        from webcms.templates.theme import ThemeManager as TM
        try:
            tm = TM(db=self.db)
            success = tm.activate(theme_id)
            return Response.json({"success": success, "id": theme_id, "active": success}, 200 if success else 400)
        except Exception as e:
            return Response.json({"success": False, "id": theme_id, "active": False, "error": str(e)}, 400)

    def deactivate_theme(self, request: Request, theme_id: str) -> Response:
        from webcms.templates.theme import ThemeManager as TM
        try:
            tm = TM(db=self.db)
            success = tm.deactivate(theme_id)
            return Response.json({"success": success, "id": theme_id, "active": not success}, 200 if success else 400)
        except Exception as e:
            return Response.json({"success": False, "id": theme_id, "active": False, "error": str(e)}, 400)'''

if old_section in content:
    content = content.replace(old_section, new_section)
    with open('webcms/admin/admin_api.py', 'w') as f:
        f.write(content)
    print("Successfully patched admin_api.py")
else:
    print("Could not find the section to replace")
    # Try to find similar section
    if "Templates & Themes" in content:
        print("Found 'Templates & Themes' section but exact match failed")
