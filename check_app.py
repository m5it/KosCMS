import os

for root, dirs, files in os.walk('webcms'):
    for f in files:
        if f.endswith('.py') and ('app' in f.lower() or 'main' in f.lower() or 'server' in f.lower() or 'factory' in f.lower()):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
            if 'create_app' in content or '__main__' in content or 'serve' in content or 'run(' in content:
                print(path)
