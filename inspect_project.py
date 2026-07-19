import os, json
from pathlib import Path

root = Path("webcms")
print("ROOT:", root.resolve())
for p in sorted(root.iterdir()):
    print(p.name, "DIR" if p.is_dir() else "file")

print("\nPython files in root:")
for p in root.glob("*.py"):
    print(p)

print("\nLooking for __main__ or app/run:")
for p in root.rglob("*.py"):
    text = p.read_text(errors="ignore")
    if "__main__" in text or "app.run" in text or "run(" in text or "serve(" in text:
        print(p, "contains entry-ish")
