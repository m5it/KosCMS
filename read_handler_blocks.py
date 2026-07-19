from pathlib import Path; p = Path("webcms/admin/admin_api.py"); lines = p.read_text().splitlines()
ranges = [(397,470), (611,700), (1202,1275), (1761,1800)]
for start, end in ranges:
    print(f"\n=== LINES {start}-{end} ===")
    for i in range(start-1, min(end, len(lines))):
        print(f"{i+1:4d}: {lines[i].rstrip()}")