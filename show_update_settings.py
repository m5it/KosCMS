from pathlib import Path
p = Path("webcms/admin/admin_api.py")
lines = p.read_text().splitlines()
start = None
for i, line in enumerate(lines):
    if "def update_settings" in line:
        start = i
        break
if start is None:
    print("not found")
else:
    # print 80 lines from start
    for j in range(start, min(start+80, len(lines))):
        print(f"{j+1:4d}: {lines[j].rstrip()}")
