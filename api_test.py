import subprocess
import json

BASE = 'http://127.0.0.1:8000'

def curl(method, path, data=None):
    cmd = ['curl', '-s', '-X', method, '-i', f'{BASE}{path}']
    if data is not None:
        cmd += ['-H', 'Content-Type: application/json', '-d', json.dumps(data)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout

# Test settings get
print("=== GET /api/v1/admin/settings ===")
print(curl('GET', '/api/v1/admin/settings'))

# Test settings update (site_name)
print("\\n=== PUT /api/v1/admin/settings ===")
print(curl('PUT', '/api/v1/admin/settings', {'site_name': 'WebCMS Test Site'}))

# Verify persistence
print("\\n=== GET /api/v1/admin/settings (verify) ===")
print(curl('GET', '/api/v1/admin/settings'))
