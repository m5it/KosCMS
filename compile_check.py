import py_compile, sys
try: py_compile.compile("webcms/admin/admin_api.py", doraise=True); print("OK")
except Exception as e: print("COMPILE ERROR:", e); sys.exit(1)