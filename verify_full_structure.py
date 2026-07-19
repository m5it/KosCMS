from pathlib import Path

p = Path("webcms/admin/admin_api.py")
lines = p.read_text().splitlines()

# Check the structure - find key markers
markers = []
for i, line in enumerate(lines):
    if "def update_settings" in line:
        markers.append(("update_settings start", i+1))
    if "if self._is_kosdb():" in line and i > 1300:
        markers.append(("KosDB check", i+1))
    if "if hasattr(self.db, 'transaction'):" in line:
        markers.append(("transaction check", i+1))
    if "with self.db.transaction() as conn:" in line:
        markers.append(("transaction context", i+1))
    if "# FALLBACK: Raw dict-style db" in line:
        markers.append(("fallback path", i+1))
    if "else:" in line and i > 1370 and i < 1450:
        markers.append(("SQLAlchemy else", i+1))
    if "session.commit()" in line and i > 1400:
        markers.append(("SQLAlchemy commit", i+1))

print("Key markers found:")
for name, line_no in markers:
    print(f"  {name}: line {line_no}")

# Verify syntax
import ast
try:
    ast.parse(p.read_text())
    print("\nSyntax: OK")
except SyntaxError as e:
    print(f"\nSyntax error: {e}")
