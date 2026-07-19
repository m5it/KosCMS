from pathlib import Path

p = Path("SETTINGS_PERFORMANCE_ISSUES.md")
content = p.read_text()
lines = content.splitlines()

print(f"Total lines: {len(lines)}")
print(f"\nLast 30 lines:")
for i in range(max(0, len(lines)-30), len(lines)):
    print(f"{i+1:4d}: {lines[i][:80]}")
