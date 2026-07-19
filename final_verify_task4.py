from pathlib import Path
import ast

p = Path("webcms/database/kosdb_client.py")
content = p.read_text()

print("=== KosDBConfig max_ping_interval ===")
for i, line in enumerate(content.splitlines()):
    if "max_ping_interval" in line:
        print(f"  Line {i+1}: {line.strip()}")

print("\n=== acquire() ping skip logic ===")
lines = content.splitlines()
for i, line in enumerate(lines):
    if "def acquire(self)" in line:
        for j in range(i, min(i+25, len(lines))):
            if "ping" in lines[j].lower() or "time_since" in lines[j]:
                print(f"  Line {j+1}: {lines[j].strip()}")
        break

print("\n=== last_used updates ===")
for i, line in enumerate(lines):
    if "last_used" in line:
        print(f"  Line {i+1}: {line.strip()}")

# Verify syntax
try:
    ast.parse(content)
    print("\nSyntax: OK")
except SyntaxError as e:
    print(f"\nSyntax error: {e}")
