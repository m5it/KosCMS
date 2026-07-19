from pathlib import Path
p = Path("webcms/core/router.py")
for i, line in enumerate(p.read_text().splitlines(keepends=True), 1):
    if 40 <= i <= 60:
        print(f"{i:3d}: {line!r}")