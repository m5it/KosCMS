from pathlib import Path; p = Path("webcms/core/router.py"); txt = p.read_text()
idx = txt.find("def _compile_pattern")
print(repr(txt[idx:idx+600]))