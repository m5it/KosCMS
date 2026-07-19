path = "webcms/app_factory.py"
with open(path) as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'middleware' in line.lower() or 'SecurityMiddleware' in line or 'HTTPSRedirectMiddleware' in line or 'CORS' in line:
        print(f"{i:4d}: {line.rstrip()[:160]}")
