import os

for root, dirs, files in os.walk('webcms'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
            if 'if __name__' in content and ('create_app' in content or 'Application(' in content or 'make_server' in content):
                print(path)
