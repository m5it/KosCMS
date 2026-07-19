from pathlib import Path
import os
for root, dirs, files in os.walk('webcms'):
    for f in files:
        if f.endswith('.py') and ('run' in f.lower() or 'server' in f.lower() or 'main' in f.lower() or 'wsgi' in f.lower() or 'asgi' in f.lower()):
            print(os.path.join(root, f))
