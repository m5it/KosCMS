from pathlib import Path; p = Path("webcms/admin/admin_api.py"); lines = p.read_text().splitlines()
in_reg = False
for i, line in enumerate(lines, 1):
    if "def register_admin_api" in line: in_reg = True
    if in_reg:
        print(f"{i:4d}: {line}")
        if line.strip().startswith("return") and not line.strip().startswith("return Response"):
            break
