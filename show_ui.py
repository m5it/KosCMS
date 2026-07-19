path = "webcms/admin-ui/src/admin/pages/TemplateManager.jsx"
with open(path) as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    print(f"{i:4d}: {line.rstrip()}")
