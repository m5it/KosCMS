from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines()

for i, line in enumerate(lines):
    if "def acquire" in line or ("@contextmanager" in line and i > 240):
        print(f"{i+1:4d}: {line}")
        for j in range(i+1, min(i+40, len(lines))):
            print(f"{j+1:4d}: {lines[j]}")
        break
