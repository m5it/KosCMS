import py_compile

files = [
    'webcms/admin/admin_api.py',
    'webcms/app_factory.py',
    'webcms/templates/engine.py',
]

for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"{f}: OK")
    except Exception as e:
        print(f"{f}: FAIL - {e}")
