from pathlib import Path; p = Path("webcms/admin/api.py"); txt = p.read_text()
for i, line in enumerate(txt.splitlines(), 1):
    if "route" in line.lower() or "register" in line.lower() or "admin" in line.lower() or "api" in line.lower():
        print(f"{i:4d}: {line}")