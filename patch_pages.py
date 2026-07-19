from pathlib import Path
p = Path("webcms/admin/admin_api.py")
lines = p.read_text().splitlines(keepends=True)

# Find create_page and update_page blocks and replace db usage
# create_page: manager = ContentManager(self.db) -> manager = ContentManager(self._sa_session())
# update_page: manager = ContentManager(self.db) -> manager = ContentManager(self._sa_session())
for i, line in enumerate(lines):
    if "manager = ContentManager(self.db)" in line:
        lines[i] = line.replace("ContentManager(self.db)", "ContentManager(self._sa_session())")
        print(f"replaced line {i+1}")
with open(str(p), "w") as f: f.writelines(lines)
print("patched pages")