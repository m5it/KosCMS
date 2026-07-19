from pathlib import Path; p = Path("webcms/admin/api.py"); txt = p.read_text(); in_func = False
for i, line in enumerate(txt.splitlines(), 1):
    if "def create_api" in line: in_func = True
    if in_func:
        print(f"{i:4d}: {line}")
        if line.strip() == "" and i > 510 and not line.startswith("def "): pass
        if in_func and line.strip().startswith("return") and i > 520: break