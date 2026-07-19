import subprocess
import time

r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://127.0.0.1:8000/admin'], capture_output=True, text=True)
print("HTTP status /admin:", r.stdout, r.stderr)

r2 = subprocess.run(['curl', '-s', 'http://127.0.0.1:8000/api/v1/admin/settings'], capture_output=True, text=True)
print("Settings response:", r2.stdout[:500])
