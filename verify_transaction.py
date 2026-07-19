from pathlib import Path
p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines()

# Find transaction method
for i, line in enumerate(lines):
    if "def transaction(self):" in line:
        print(f"Found transaction() at line {i+1}")
        # Print from that line to end
        for j in range(i, min(i+60, len(lines))):
            print(f"{j+1:4d}: {lines[j]}")
        break
else:
    print("transaction() method not found")
