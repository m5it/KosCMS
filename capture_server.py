import subprocess
import time
import sys
import select

server = subprocess.Popen(
    ['python3', 'run_server.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

time.sleep(3)
print("Server output so far:")
ready, _, _ = select.select([server.stdout], [], [], 0.5)
while ready:
    line = server.stdout.readline()
    if not line:
        break
    print(line, end='')
    ready, _, _ = select.select([server.stdout], [], [], 0.1)

server.terminate()
