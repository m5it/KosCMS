from pathlib import Path
files = ["webcms/content/manager.py", "webcms/templates/engine.py", "webcms/plugins/marketplace.py"]
for f in files:
    print("\n===", f, "===")
    with open(f) as fh: txt = fh.read()
    for i, line in enumerate(txt.splitlines(), 1):
        if any(k in line for k in ["def create_page", "def update_page", "def save_template", "def activate", "def deactivate", "def list_available"]): print(f"{i:4d}: {line}")