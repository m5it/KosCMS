import subprocess
import time
import json
import re
import os
import signal

BASE = 'http://127.0.0.1:8000'

def curl(method, path, data=None):
    cmd = ['curl', '-s', '-X', method, '-i', f'{BASE}{path}']
    if data is not None:
        cmd += ['-H', 'Content-Type: application/json', '-d', json.dumps(data)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout

# Kill existing server
subprocess.run(['pkill', '-f', 'run_server.py'])
subprocess.run(['pkill', '-f', 'run_server_log.py'])
time.sleep(1)

# Start server with log file
log = open('/tmp/webcms_server.log', 'w')
server = subprocess.Popen(
    ['python3', 'run_server.py'],
    stdout=log,
    stderr=subprocess.STDOUT
)

time.sleep(3)

print('=== GET /admin ===')
print(curl('GET', '/admin')[:200])

print('\\n=== PUT /api/v1/admin/settings ===')
print(curl('PUT', '/api/v1/admin/settings', {'site_name': 'WebCMS Test Site'})[:300])

print('\\n=== POST /api/v1/admin/templates ===')
print(curl('POST', '/api/v1/admin/templates', {'id': 'test_template', 'name': 'test_template.html', 'content': '<h1>Test</h1>'})[:300])

print('\\n=== POST /api/v1/admin/pages ===')
print(curl('POST', '/api/v1/admin/pages', {'title': 'Test Page', 'slug': 'test-page', 'content': 'Hello world', 'status': 'published', 'author_id': '1'})[:300])

server.send_signal(signal.SIGTERM)
server.wait(timeout=5)
log.close()

print('\\n=== Server log tail ===')
with open('/tmp/webcms_server.log') as f:
    lines = f.readlines()
for line in lines[-100:]:
    print(line, end='')
