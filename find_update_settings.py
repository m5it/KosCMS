from pathlib import Path

p = Path("webcms/admin/admin_api.py")
lines = p.read_text().splitlines()

for i, line in enumerate(lines):
    if "def update_settings" in line:
        print(f"Found update_settings at line {i+1}")
        # Print context around it
        start = max(0, i-5)
        end = min(len(lines), i+150)
        for j in range(start, end):
            print(f"{j+1:4d}: {lines[j]}")
        break
