from pathlib import Path
p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines()

# Check around line 485
print("Lines 480-560:")
for i in range(479, min(560, len(lines))):
    print(f"{i+1:4d}: {lines[i]}")
