from pathlib import Path
import ast

p = Path("webcms/database/kosdb_client.py")
content = p.read_text()

# Check for duplicate transaction methods
count = content.count("def transaction(self):")
print(f"Number of transaction methods: {count}")

# Check file structure
lines = content.splitlines()
print(f"Total lines: {len(lines)}")

# Find class structure
in_kosdbclient = False
methods = []
for i, line in enumerate(lines):
    if "class KosDBClient:" in line:
        in_kosdbclient = True
        continue
    if in_kosdbclient:
        if line.startswith("class "):
            break
        if "def " in line and "    def " in line:
            method_name = line.strip().split("(")[0].replace("def ", "")
            methods.append((i+1, method_name))

print("\nKosDBClient methods:")
for line_no, name in methods:
    print(f"  Line {line_no}: {name}")

# Verify syntax
try:
    ast.parse(content)
    print("\nSyntax OK")
except SyntaxError as e:
    print(f"\nSyntax error: {e}")
