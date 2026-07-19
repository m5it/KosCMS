path = "webcms/content/manager.py"
with open(path) as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'def create_page' in line or 'def update_page' in line:
        print(f"{i:4d}: {line.rstrip()}")
