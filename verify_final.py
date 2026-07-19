from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines()

# Find transaction method
start = None
for i, line in enumerate(lines):
    if "def transaction(self):" in line:
        start = i
        break

print("transaction() method:")
for i in range(start, min(start + 85, len(lines))):
    print(f"{i+1:4d}: {lines[i]}")

print(f"\nFile ends at line {len(lines)}")
