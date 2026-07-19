from pathlib import Path
p = Path("webcms/admin/admin_api.py")
txt = p.read_text()
# Decode Python string escapes (\\n -> newline, \\\" -> ")
decoded = txt.encode("utf-8").decode("unicode_escape")
p.write_text(decoded)
print("decoded escapes")