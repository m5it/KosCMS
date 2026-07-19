path = "webcms/cli/commands.py"
with open(path) as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'serve' in line.lower() or 'run' in line.lower() or 'create_app' in line or 'make_server' in line or '__main__' in line:
        print(f"{i:4d}: {line.rstrip()}")
