from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines()

print("=== acquire() method ===")
for i, line in enumerate(lines):
    if "def acquire(self)" in line:
        for j in range(i, min(i+50, len(lines))):
            print(f"{j+1:4d}: {lines[j]}")
        break
