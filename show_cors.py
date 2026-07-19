path = "webcms/core/middleware.py"
with open(path) as f:
    lines = f.readlines()

for i in range(160, 200):
    print(f"{i+1:4d}: {lines[i].rstrip()}")
