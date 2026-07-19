from pathlib import Path; p = Path("webcms/admin/admin_api.py"); lines = p.read_text().splitlines()
for i in range(245, 275):
    print(f"{i+1:4d}: {repr(lines[i])}")