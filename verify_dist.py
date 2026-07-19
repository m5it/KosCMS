import os
from pathlib import Path

dist = Path('webcms/admin-ui/dist')
print("dist exists:", dist.exists())
print("index.html exists:", (dist / 'index.html').exists())
for f in sorted(dist.glob('assets/*')):
    print("asset:", f.name, f.stat().st_size)
