from pathlib import Path
p = Path("verify_all.py")
lines = p.read_text().splitlines(keepends=True)
# remove the duplicate admin ui line
new_lines = [line for line in lines if not ('("admin ui"' in line and '"Admin UI" in b' in line)]
p.write_text("".join(new_lines))
print("removed duplicate")