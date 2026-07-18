#!/usr/bin/env python3
"""Fix the list_templates method in admin_api.py"""

with open('webcms/admin/admin_api.py', 'r') as f:
    content = f.read()

old_code = '''    def list_templates(self, request: Request) -> Response:
        from webcms.templates.engine import TemplateEngine
        try:
            engine = TemplateEngine(db=self.db)'''

new_code = '''    def list_templates(self, request: Request) -> Response:
        from webcms.templates.engine import TemplateEngine
        from webcms.templates.theme import ThemeManager
        try:
            # Get template directories from active theme
            tm = ThemeManager(db=self.db)
            template_dirs = tm.get_template_dirs()
            engine = TemplateEngine(template_dirs=template_dirs, db=self.db)'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('webcms/admin/admin_api.py', 'w') as f:
        f.write(content)
    print("Successfully patched list_templates")
else:
    print("Could not find the code to replace")
