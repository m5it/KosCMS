from pathlib import Path
p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines()

# Check lines 560-600
print("Lines 560-600:")
for i in range(559, min(600, len(lines))):
    print(f"{i+1:4d}: {lines[i]}")
