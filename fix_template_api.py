path = "webcms/admin/admin_api.py"
with open(path) as f:
    src = f.read()

# Fix create_template to pass template_dirs
old_create = '''    def create_template(self, request: Request) -> Response:
        from webcms.templates.engine import TemplateEngine
        data = request.json or {}
        if not data:
            return Response.error("Invalid JSON", 400)
        try:
            engine = TemplateEngine(db=self.db)
            raw_id = data.get("id") or data.get("name") or str(uuid.uuid4())'''

new_create = '''    def create_template(self, request: Request) -> Response:
        from webcms.templates.engine import TemplateEngine
        from webcms.templates.theme import ThemeManager
        data = request.json or {}
        if not data:
            return Response.error("Invalid JSON", 400)
        try:
            tm = ThemeManager(db=self.db)
            template_dirs = tm.get_template_dirs()
            engine = TemplateEngine(template_dirs=template_dirs, db=self.db)
            raw_id = data.get("id") or data.get("name") or str(uuid.uuid4())'''

src = src.replace(old_create, new_create)

# Fix update_template to pass template_dirs
old_update = '''    def update_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        data = request.json or {}
        try:
            engine = TemplateEngine(db=self.db)
            result = engine.save_template(template_id, data.get("content", ""), name=data.get("name"))'''

new_update = '''    def update_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        from webcms.templates.theme import ThemeManager
        data = request.json or {}
        try:
            tm = ThemeManager(db=self.db)
            template_dirs = tm.get_template_dirs()
            engine = TemplateEngine(template_dirs=template_dirs, db=self.db)
            result = engine.save_template(template_id, data.get("content", ""), name=data.get("name"))'''

src = src.replace(old_update, new_update)

# Fix delete_template to pass template_dirs
old_delete = '''    def delete_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        try:
            engine = TemplateEngine(db=self.db)
            if engine.delete_template(template_id):'''

new_delete = '''    def delete_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        from webcms.templates.theme import ThemeManager
        try:
            tm = ThemeManager(db=self.db)
            template_dirs = tm.get_template_dirs()
            engine = TemplateEngine(template_dirs=template_dirs, db=self.db)
            if engine.delete_template(template_id):'''

src = src.replace(old_delete, new_delete)

with open(path, "w") as f:
    f.write(src)
print("fixed template api")
