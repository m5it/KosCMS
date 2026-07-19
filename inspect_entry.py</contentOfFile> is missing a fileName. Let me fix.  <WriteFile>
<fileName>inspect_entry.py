from pathlib import Path; files = ["webcms/app_factory.py", "webcms/cli.py", "webcms/core/application.py"]
for f in files:
    print("===", f, "===")
    if not Path(f).exists(): print("missing"); continue
    with open(f) as fh: lines = fh.readlines()
    for i, line in enumerate(lines[:80], 1): print(f"{i:3d}: {line.rstrip()}")