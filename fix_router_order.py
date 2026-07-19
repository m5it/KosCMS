from pathlib import Path
p = Path("webcms/core/router.py")
lines = p.read_text().splitlines(keepends=True)
for i, line in enumerate(lines):
    if "# Convert {param:path}" in line:
n        # Insert Flask-style handling before brace handling\n        # Replace the whole _compile_pattern body\n        start = i - 1  # line before comment\n        while start > 0 and lines[start-1].strip() != \"return re.compile\":\n            pass\n