from pathlib import Path
p = Path("verify_all.py")
lines = p.read_text().splitlines(keepends=True)
for i, line in enumerate(lines):
    if '("admin ui"' in line:
        lines[i] = '    ("admin ui", lambda s, b: s == 200 and "WebCMS Admin" in b, ("GET", "/admin", None, False)),\n'
        print(f"fixed line {i+1}")
        break
    if '("pages list"' in line and '"pages" in b' not in line:
        lines[i] = '    ("pages list", lambda s, b: s == 200 and "pages" in b, ("GET", "/api/v1/admin/pages", None, True)),\n'
        print(f"fixed pages list line {i+1}")
p.write_text("".join(lines))