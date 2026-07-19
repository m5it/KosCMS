import subprocess
import time
import json
import sys
import re

BASE = 'http://127.0.0.1:8000'

def curl(method, path, data=None):
    cmd = ['curl', '-s', '-X', method, '-i', f'{BASE}{path}']
    if data is not None:
        cmd += ['-H', 'Content-Type: application/json', '-d', json.dumps(data)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout

print("Starting server...")
server = subprocess.Popen(
    ['python3', 'run_server.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Wait for server to start
for _ in range(30):
    line = server.stdout.readline()
    if line:
        print(line, end='')
    if 'Running on' in line or 'Serving on' in line or '127.0.0.1' in line:
        break
    time.sleep(0.2)

print("\n=== Test 1: GET /admin ===")
print(curl('GET', '/admin')[:500])

print("\n=== Test 2: GET /api/v1/admin/settings ===")
print(curl('GET', '/api/v1/admin/settings'))

print("\n=== Test 3: PUT /api/v1/admin/settings (change site_name) ===")
print(curl('PUT', '/api/v1/admin/settings', {'site_name': 'WebCMS Test Site'}))

print("\n=== Test 4: GET /api/v1/admin/settings (verify persistence) ===")
print(curl('GET', '/api/v1/admin/settings'))

print("\n=== Test 5: POST /api/v1/admin/pages (create page) ===")
create_page = curl('POST', '/api/v1/admin/pages', {'title': 'Test Page', 'slug': 'test-page', 'content': 'Hello world', 'status': 'published'})
print(create_page)

print("\n=== Test 6: PUT /api/v1/admin/pages/{id} (update page) ===")
m = re.search(r'"id"\s*:\s*"([^"]+)"', create_page)
page_id = m.group(1) if m else '1'
print(curl('PUT', f'/api/v1/admin/pages/{page_id}', {'title': 'Updated Page', 'content': 'Updated content'}))

print("\n=== Test 7: GET /api/v1/admin/plugins ===")
print(curl('GET', '/api/v1/admin/plugins'))

print("\n=== Test 8: POST /api/v1/admin/templates (create template) ===")
print(curl('POST', '/api/v1/admin/templates', {'id': 'test_template', 'name': 'test_template.html', 'content': '<h1>Test</h1>'}))

print("\n=== Test 9: PUT /api/v1/admin/templates/test_template (update template) ===")
print(curl('PUT', '/api/v1/admin/templates/test_template', {'content': '<h1>Updated</h1>'}))

print("\n=== Test 10: GET /api/v1/admin/templates (list templates) ===")
print(curl('GET', '/api/v1/admin/templates'))

server.terminate()
