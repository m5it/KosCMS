import os

for root, dirs, files in os.walk('webcms'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
            if 'CORSMiddleware' in content or 'cors' in content.lower():
                print(f"== {path} ==")
                for i, line in enumerate(content.splitlines(), 1):
                    if 'CORSMiddleware' in line or 'cors' in line.lower():
                        print(f"  {i}: {line.rstrip()[:160]}")
