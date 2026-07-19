from pathlib import Path

p = Path("webcms/admin/admin_api.py")
lines = p.read_text().splitlines()

# Show the control flow structure
print("Control flow structure around update_settings:")
for i in range(1318, 1455):
    line = lines[i]
    indent = len(line) - len(line.lstrip())
    print(f"{i+1:4d}: {'  ' * (indent // 4)}{line.strip()[:70]}")
