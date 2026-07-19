from pathlib import Path
files = ["webcms/content/manager.py", "webcms/templates/engine.py", "webcms/plugins/marketplace.py"]
for f in files:
    print("\n===", f, "===")
    if not Path(f).exists(): print("missing"); continue
    with open(f) as fh: lines = fh.readlines()
    for i, line in enumerate(lines[:60], 1): print(f"{i:3d}: {line.rstrip()}")