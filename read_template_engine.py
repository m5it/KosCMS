from pathlib import Path; p = Path("webcms/templates/engine.py"); lines = p.read_text().splitlines()
for i in range(60, 180):
    print(f"{i+1:4d}: {lines[i].rstrip()}")