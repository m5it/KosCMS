path = "webcms/admin/admin_api.py"
with open(path) as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'def update_settings' in line or 'Using SQLAlchemy path' in line:
        print(f"{i:4d}: {line.rstrip()}")
