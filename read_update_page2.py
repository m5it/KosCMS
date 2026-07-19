from pathlib import Path; p = Path("webcms/admin/admin_api.py"); lines = p.read_text().splitlines()
for i in range(461, 495):
    print(f"{i+1:4d}: {lines[i].rstrip()}")