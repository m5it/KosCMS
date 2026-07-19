from pathlib import Path; p = Path("webcms/admin/admin_api.py"); lines = p.read_text().splitlines()
for i, line in enumerate(lines, 1):
    if any(k in line for k in ["def get_settings", "def update_settings", "def list_pages", "def create_page", "def update_page", "def list_plugins", "def activate_plugin", "def deactivate_plugin", "def list_templates", "def create_template", "def update_template", "def register_admin_api"]):
        print(f"{i:4d}: {line}")