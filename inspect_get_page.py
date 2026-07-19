from pathlib import Path; p = Path("webcms/content/manager.py"); lines = p.read_text().splitlines()
for i, line in enumerate(lines, 1):
    if "def get_page" in line:
        print(f"{i:4d}: {line}")
        for j in range(i, min(i+20, len(lines))): print(f"{j+1:4d}: {lines[j].rstrip()}")
        break