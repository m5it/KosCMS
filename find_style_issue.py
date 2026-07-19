import os

for root, dirs, files in os.walk('webcms/admin-ui/src'):
    for f in files:
        if f.endswith(('.jsx', '.js', '.css')):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
            if r'\\n' in content:
                print(f"Found escaped newlines in {path}")
                for i, line in enumerate(content.splitlines(), 1):
                    if r'\\n' in line:
                        print(f"  {i}: {line[:200]}")
