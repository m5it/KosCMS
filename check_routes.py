from pathlib import Path

js = Path('webcms/admin-ui/dist/assets/index-CXukPda6.js').read_text()
routes = ['/admin/dashboard', '/admin/content', '/admin/media', '/admin/templates', '/admin/themes', '/admin/plugins', '/admin/users', '/admin/roles', '/admin/settings', '/admin/cache', '/admin/backups', '/admin/workflows', '/admin/tenants', '/admin/search', '/admin/notifications']
apis = ['/api/v1/admin/templates', '/api/v1/admin/content', '/api/v1/admin/users', '/api/v1/admin/settings', '/api/v1/admin/plugins', '/api/v1/admin/themes']
print("=== Routes ===")
for r in routes:
    print(f"{r}: {'found' if r in js else 'MISSING'}")
print("=== API paths ===")
for a in apis:
    print(f"{a}: {'found' if a in js else 'MISSING'}")
