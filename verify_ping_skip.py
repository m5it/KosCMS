from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines()

print("=== KosDBConfig (checking max_ping_interval) ===")
for i, line in enumerate(lines):
    if "max_ping_interval" in line:
        print(f"{i+1:4d}: {line}")

print("\n=== acquire() method (checking ping skip logic) ===")
in_acquire = False
for i, line in enumerate(lines):
    if "def acquire(self)" in line:
        in_acquire = True
        start = i
    if in_acquire:
        print(f"{i+1:4d}: {line}")
        if i > start + 35:
            break

print("\n=== Verify last_used is updated in execute() ===")
for i, line in enumerate(lines):
    if "self.last_used = time.time()" in line:
        print(f"{i+1:4d}: {line}")
