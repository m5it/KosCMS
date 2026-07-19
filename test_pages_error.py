import subprocess
import time
import json

BASE = 'http://127.0.0.1:8000'

subprocess.run(['pkill', '-f', 'run_server.py'])
time.sleep(1)

server = subprocess.Popen(
    ['python3', 'run_server.py'],
    stdout=open('/tmp/webcms_server.log', 'w'),
    stderr=subprocess.STDOUT
)

time.sleep(3)

cmd = ['curl', '-s', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps({'title': 'Test Page', 'slug': 'test-page', 'content': 'Hello world', 'status': 'published', 'author_id': '1'}), f'{BASE}/api/v1/admin/pages']
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stdout)

server.terminate()
