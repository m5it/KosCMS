path = "webcms/app_factory.py"
with open(path) as f:
    lines = f.readlines()

for i in range(110, 150):
    print(f"{i+1:4d}: {lines[i].rstrip()}")
