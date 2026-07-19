from pathlib import Path

p = Path("webcms/admin/admin_api.py")
lines = p.read_text().splitlines()

# Find the update_settings method and show the KosDB path
in_update_settings = False
kosdb_section = []
for i, line in enumerate(lines):
    if "def update_settings" in line:
        in_update_settings = True
        start = i
    if in_update_settings:
        kosdb_section.append(f"{i+1:4d}: {line}")
        if i > start + 100:  # Show first 100 lines of the method
            break

print("update_settings method (KosDB path):")
for line in kosdb_section[15:80]:  # Focus on the KosDB logic
    print(line)
