import sys; sys.path.insert(0, "webcms")
from webcms.core.router import Router
r = Router()
try:
    pat = r._compile_pattern("/admin/{filename:path}")
    print("OK", pat.pattern)
except Exception as e:
    print("ERROR", e)
try:
    pat = r._compile_pattern("/api/v1/admin/plugins/<plugin_id>/activate")
    print("OK", pat.pattern)
except Exception as e:
    print("ERROR", e)