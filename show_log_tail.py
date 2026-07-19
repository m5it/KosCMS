import subprocess
r = subprocess.run(['tail', '-40', '/tmp/webcms_server.log'], capture_output=True, text=True)
print(r.stdout)
