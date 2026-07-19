import re

path = "webcms/admin/admin_api.py"
with open(path) as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if "template" in line.lower() or "TemplateEngine" in line:
        print(f"{i:4d}: {line.rstrip()}")
