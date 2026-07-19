import subprocess
import time
import json
import re

BASE = 'http://127.0.0.1:8000'

def curl(method, path, data=None):
    cmd = ['curl', '-s', '-X', method, '-i', f'{BASE}{path}']
    if data is not None:
        cmd += ['-H', 'Content-Type: application/json', '-d', json.dumps(data)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout

subprocess.run(['pkill', '-f', 'run_server_log.py'])

server = subprocess.Popen(
    ['python3', 'run_server_log.py'],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

time.sleep(3)

def run_tests():
    results = {}
    results['admin_index'] = curl('GET', '/admin')[:300]
    results['settings_get'] = curl('GET', '/api/v1/admin/settings')
    results['settings_put'] = curl('PUT', '/api/v1/admin/settings', {'site_name': 'WebCMS Test Site'})
    results['settings_get2'] = curl('GET', '/api/v1/admin/settings')
    results['pages_create'] = curl('POST', '/api/v1/admin/pages', {'title': 'Test Page', 'slug': 'test-page', 'content': 'Hello world', 'status': 'published', 'author_id': '1'})
    m = re.search(r'\"id\"\\s*:\\s*\"([^\"]+)\"', results['pages_create'])
    page_id = m.group(1) if m else '1'
    results['pages_update'] = curl('PUT', f'/api/v1/admin/pages/{page_id}', {'title': 'Updated Page', 'content': 'Updated content'})
    results['plugins_list'] = curl('GET', '/api/v1/admin/plugins')
    results['template_create'] = curl('POST', '/api/v1/admin/templates', {'id': 'test_template', 'name': 'test_template.html', 'content': '<h1>Test</h1>'})
    results['template_update'] = curl('PUT', '/api/v1/admin/templates/test_template', {'content': '<h1>Updated</h1>'})
    results['template_list'] = curl('GET', '/api/v1/admin/templates')
    return results

results = run_tests()
for name, body in results.items():
    print(f"\n=== {name} ===")
    print(body[:800])

server.terminate()

# Print log tail
print("\n=== server.log tail ===")
with open('server.log') as f:
    lines = f.readlines()
for line in lines[-80:]:
    print(line, end='')
