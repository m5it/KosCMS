from pathlib import Path
root = Path("webcms")
# Look for __main__.py and server startup files
for p in root.rglob("*.py"):
    txt = p.read_text(errors="ignore")
    if "make_hardened_server" in txt or "__main__" in txt or "make_server" in txt or "serve_forever" in txt:
        print(p, "contains relevant code")
