from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines()

print("=== ping() method area (lines 255-280) ===")
for i in range(254, 280):
    print(f"{i+1:4d}: {lines[i]}")
