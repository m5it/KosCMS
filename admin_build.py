import subprocess
import os
import sys

os.chdir('webcms/admin-ui')

if not os.path.exists('node_modules'):
    print("node_modules missing, running npm install...")
    r = subprocess.run(['npm', 'install'], capture_output=True, text=True)
    print(r.stdout)
    print(r.stderr)
    if r.returncode != 0:
        sys.exit(1)

print("Running npm run build...")
r = subprocess.run(['npm', 'run', 'build'], capture_output=True, text=True)
print(r.stdout)
print(r.stderr)
sys.exit(r.returncode)
