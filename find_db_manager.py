import os

for root, dirs, files in os.walk('webcms'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
            if 'class DatabaseManager' in content:
                print(path)
                for i, line in enumerate(content.splitlines(), 1):
                    if 'class DatabaseManager' in line or 'def execute' in line or 'def query' in line or 'def session' in line:
                        print(f"  {i}: {line.rstrip()}")
