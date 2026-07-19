path = "webcms/admin-ui/src/admin/admin.css"
with open(path) as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if r'\\n' in line or 'n    width: 100%' in line:
        print(f"{i:4d}: {line.rstrip()[:200]}")
