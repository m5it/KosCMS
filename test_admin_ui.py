import urllib.request, os; base=os.environ.get("WEBCMS_BASE","http://127.0.0.1:43805")
for path in ["/admin", "/admin/"]:
    try:
        with urllib.request.urlopen(base + path, timeout=3) as r:
            print(path, r.status, len(r.read()))
    except Exception as e:
        print(path, "error:", e)