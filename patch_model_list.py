from pathlib import Path
p = Path("webcms/admin/admin_api.py")
lines = p.read_text().splitlines(keepends=True)

# Fix _get_model_list SQLAlchemy branch: self.db.query -> session.query
for i, line in enumerate(lines):
    if "query = self.db.query(model_class)" in line:
        # Replace this line and following lines in the else branch to use session
        lines[i] = "        else:\\n"
        # find indentation: this is inside _get_model_list, we need to rewrite the else block
        # Actually simpler: replace self.db.query with session = self._sa_session(); query = session.query
        # But we also need to close session. Let's replace the specific line.
        lines[i] = "            session = self._sa_session()\\n            try:\\n                query = session.query(model_class)\\n"
        # Now we need to add session.close() after the query is executed. Find the return in this block.
        # Look for the line with `.all()` or `.count()` etc. Hard to automate safely.
        print(f"replaced line {i+1}")
with open(str(p), "w") as f: f.writelines(lines)
print("patched model_list partial")