import py_compile

files = [
    'webcms/models/system.py',
]

for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"{f}: OK")
    except Exception as e:
        print(f"{f}: FAIL - {e}")
