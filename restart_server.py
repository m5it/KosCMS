import subprocess, time, os, sys, socket, json, urllib.request, signal; root = os.path.dirname(os.path.abspath(__file__)); os.chdir(root)
try:
    for pid in [int(x) for x in subprocess.check_output(["pgrep", "-f", "webcms.cli.commands serve"]).decode().split() if x]:
        try: os.kill(pid, signal.SIGTERM)
        except Exception: pass
    time.sleep(1)
except Exception: pass
s = socket.socket(); s.bind(("", 0)); port = s.getsockname()[1]; s.close()
env = os.environ.copy(); env["WEBCMS_PORT"] = str(port); env["WEBCMS_DB"] = "sqlite:///webcms_test.db"
proc = subprocess.Popen([sys.executable, "-m", "webcms.cli.commands", "serve", "--host", "127.0.0.1", "--port", str(port), "--debug"], env=env, stdout=open("server_out.log", "w"), stderr=subprocess.STDOUT)
base = f"http://127.0.0.1:{port}"
for i in range(40):
    try: urllib.request.urlopen(base + "/", timeout=1); break
    except Exception: time.sleep(0.5)
else: print("server did not start"); proc.terminate(); sys.exit(1)
print(json.dumps({"pid": proc.pid, "port": port, "base": base}))