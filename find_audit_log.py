import os

for root, dirs, files in os.walk('webcms/models'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
            if 'AuditLog' in content:
                print(path)
                for i, line in enumerate(content.splitlines(), 1):
                    if 'class AuditLog' in line or 'user_id' in line or 'user =' in line:
                        print(f"  {i}: {line.rstrip()}")
