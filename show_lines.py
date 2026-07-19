import sys
path = "webcms/templates/engine.py"
with open(path) as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    print(f"{i:4d}: {line.rstrip()}")
