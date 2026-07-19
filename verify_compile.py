import py_compile
import os

files = [
    "webcms/templates/engine.py",
    "webcms/admin/admin_api.py",
]

for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"{f}: OK")
    except Exception as e:
        print(f"{f}: FAIL - {e}")
        os._exit(1)
