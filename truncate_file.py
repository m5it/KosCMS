from pathlib import Path

p = Path("SETTINGS_PERFORMANCE_ISSUES.md")
content = p.read_text()

# Find where the old content starts (the duplicate "Issue 1" section)
marker = "## Issue 1: CMS — N+1 Query Problem"

if marker in content:
    # Find the last occurrence (the duplicate at the end)
    last_pos = content.rfind(marker)
    if last_pos > 100:  # Make sure it's not the beginning
        new_content = content[:last_pos].rstrip()
        p.write_text(new_content)
        print(f"Truncated file at position {last_pos}")
    else:
        print("Marker at beginning, no truncation needed")
else:
    print("Marker not found")
