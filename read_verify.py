from pathlib import Path; p = Path("verify_all.py"); lines = p.read_text().splitlines()
for i, line in enumerate(lines, 1):
    print(f"{i:3d}: {line.rstrip()}")