from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines()

# Check the transaction method structure
print("Lines around transaction method:")
for i in range(480, 580):
    prefix = lines[i][:12].replace(" ", "·")
    print(f"{i+1:4d}: {prefix}|{lines[i][12:][:50]}")

print("\n--- Checking class nesting ---")
# The _ReconnectingConnection should be indented more than transaction
# Let's check line 523 which shows __init__ - should be 8+ spaces
for i in [522, 523, 524]:
    line = lines[i]
    indent = len(line) - len(line.lstrip())
    print(f"Line {i+1}: {indent} spaces indent: {line[:60]}...")
