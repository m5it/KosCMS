import os

terms = ['CORS', 'cors', 'Access-Control', 'Content-Security-Policy', 'csp', 'admin', 'static']
for root, dirs, files in os.walk('webcms'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
            if any(t in content for t in terms):
                print(f"== {path} ==")
                for i, line in enumerate(content.splitlines(), 1):
                    if any(t in line for t in terms):
                        print(f"  {i}: {line.rstrip()[:160]}")
