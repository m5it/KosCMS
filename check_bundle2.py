from pathlib import Path

js = Path('webcms/admin-ui/dist/assets/index-CXukPda6.js').read_text()
checks = ['/admin/templates', '/admin/content', '/admin/users', '/admin/settings', '/admin/plugins', '/admin/themes', '/api/v1/admin/', 'fetchTemplates', 'handleSave', 'handleDelete']
for c in checks:
    print(f"{c}: {'found' if c in js else 'MISSING'}")
