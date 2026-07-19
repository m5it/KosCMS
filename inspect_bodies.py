from pathlib import Path; files = {"webcms/content/manager.py": [(118,190), (160,210)], "webcms/templates/engine.py": [(380,430)], "webcms/plugins/marketplace.py": [(300,340), (494,540)]}
for f, ranges in files.items():
    print("\n===", f, "===")
    lines = Path(f).read_text().splitlines()
    for start, end in ranges:
        for i in range(start-1, min(end, len(lines))):
            print(f"{i+1:4d}: {lines[i].rstrip()}")