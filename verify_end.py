from pathlib import Path
p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines()

# Print last 20 lines
print("Last 20 lines of file:")
for i in range(max(0, len(lines)-20), len(lines)):
    print(f"{i+1:4d}: {lines[i]}")
