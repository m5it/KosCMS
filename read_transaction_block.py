from pathlib import Path
p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines()
for i, line in enumerate(lines[340:430], start=341):
    print(f"{i:4d}: {line}")
