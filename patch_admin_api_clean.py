import re

path = "webcms/admin/admin_api.py"
with open(path) as f:
    src = f.read()

# 1. Add import re
src = src.replace(
    "import json\nimport logging\nimport uuid\nfrom datetime import datetime",
    "import json\nimport logging\nimport re\nimport uuid\nfrom datetime import datetime"
)

# 2. Fix update_settings SQLAlchemy path
old_settings = """            else:
                print("[DEBUG] Using SQLAlchemy path")
                # Use raw SQL to avoid ORM mapper configuration issues.
                from sqlalchemy import text
                for key, value in normalized.items():
                    type_ = self._guess_type(value)
                    val_str = str(value).replace("'", "''")
                    check = self.db.execute(
                        text("SELECT key FROM settings WHERE key=:key"),
                        {"key": key}
                    ).fetchone()
                    if check:
                        self.db.execute(
                            text("UPDATE settings SET value=:value, type=:type WHERE key=:key"),
                            {"key": key, "value": val_str, "type": type_}
                        )
                    else:
                        self.db.execute(
                            text("INSERT INTO settings (key, value, type) VALUES (:key, :value, :type)"),
                            {"key": key, "value": val_str, "type": type_}
                        )
                self.db.commit()

            print("[DEBUG] Settings updated successfully")
            return Response.json({"updated": True, "settings": normalized})

        except Exception as e:
            print(f"[DEBUG] Error updating settings: {e}")
            import traceback
            traceback.print_exc()
            if not self._is_kosdb():
                self.db.rollback()
            return Response.json({"updated": False, "error": str(e), "settings": data}, 400)
            return Response.json({"updated": False, "error": str(e), "settings": data}, 400)"""

new_settings = """            else:
                print("[DEBUG] Using SQLAlchemy path")
                # Use a proper session from the DatabaseManager
                from sqlalchemy import text
                session = self.db.get_session()
                try:
                    for key, value in normalized.items():
                        type_ = self._guess_type(value)
                        val_str = str(value).replace("'", "''")
                        check = session.execute(
                            text("SELECT key FROM settings WHERE key=:key"),
                            {"key": key}
                        ).fetchone()
                        if check:
                            session.execute(
                                text("UPDATE settings SET value=:value, type=:type WHERE key=:key"),
                                {"key": key, "value": val_str, "type": type_}
                            )
                        else:
                            session.execute(
                                text("INSERT INTO settings (key, value, type) VALUES (:key, :value, :type)"),
                                {"key": key, "value": val_str, "type": type_}
                            )
                    session.commit()
                except Exception:
                    session.rollback()
                    raise
                finally:
                    session.close()

            print("[DEBUG] Settings updated successfully")
            return Response.json({"updated": True, "settings": normalized})

        except Exception as e:
            print(f"[DEBUG] Error updating settings: {e}")
            import traceback
            traceback.print_exc()
            return Response.json({"updated": False, "error": str(e), "settings": data}, 400)"""

src = src.replace(old_settings, new_settings)

# 3. Fix create_page author_id
old_create_page = """            manager = ContentManager(self.db)
            page = manager.create_page(**data)
            return Response.json(self._serialize_page(page), 201)"""
new_create_page = """            manager = ContentManager(self.db)
            payload = dict(data)
            payload.setdefault('author_id', self._current_user_id(request) or 'system')
            page = manager.create_page(**payload)
            return Response.json(self._serialize_page(page), 201)"""
src = src.replace(old_create_page, new_create_page)

# 4. Fix template APIs to pass template_dirs
old_create_template = """    def create_template(self, request: Request) -> Response:
        from webcms.templates.engine import TemplateEngine
        data = request.json or {}
        if not data:
            return Response.error("Invalid JSON", 400)
        try:
            engine = TemplateEngine(db=self.db)
            raw_id = data.get("id") or data.get("name") or str(uuid.uuid4())"""
new_create_template = """    def create_template(self, request: Request) -> Response:
        from webcms.templates.engine import TemplateEngine
        from webcms.templates.theme import ThemeManager
        data = request.json or {}
        if not data:
            return Response.error("Invalid JSON", 400)
        try:
            tm = ThemeManager(db=self.db)
            template_dirs = tm.get_template_dirs()
            engine = TemplateEngine(template_dirs=template_dirs, db=self.db)
            raw_id = data.get("id") or data.get("name") or str(uuid.uuid4())"""
src = src.replace(old_create_template, new_create_template)

old_update_template = """    def update_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        data = request.json or {}
        try:
            engine = TemplateEngine(db=self.db)
            result = engine.save_template(template_id, data.get("content", ""), name=data.get("name"))"""
new_update_template = """    def update_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        from webcms.templates.theme import ThemeManager
        data = request.json or {}
        try:
            tm = ThemeManager(db=self.db)
            template_dirs = tm.get_template_dirs()
            engine = TemplateEngine(template_dirs=template_dirs, db=self.db)
            result = engine.save_template(template_id, data.get("content", ""), name=data.get("name"))"""
src = src.replace(old_update_template, new_update_template)

old_delete_template = """    def delete_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        try:
            engine = TemplateEngine(db=self.db)
            if engine.delete_template(template_id):"""
new_delete_template = """    def delete_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        from webcms.templates.theme import ThemeManager
        try:
            tm = ThemeManager(db=self.db)
            template_dirs = tm.get_template_dirs()
            engine = TemplateEngine(template_dirs=template_dirs, db=self.db)
            if engine.delete_template(template_id):"""
src = src.replace(old_delete_template, new_delete_template)

with open(path, "w") as f:
    f.write(src)
print("patched")
