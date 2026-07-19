import re
from pathlib import Path

js = Path('webcms/admin-ui/dist/assets/index-CXukPda6.js').read_text()
checks = ['TemplateManager', 'ContentManager', 'Settings', 'PluginManager', 'UserManager', 'api/v1/admin/templates', 'handleSave', 'handleDelete']
for c in checks:
    print(f"{c}: {'found' if c in js else 'MISSING'}")
