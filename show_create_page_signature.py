path = "webcms/content/manager.py"
with open(path) as f:
    lines = f.readlines()

for i in range(118, 135):
    print(f"{i+1:4d}: {lines[i].rstrip()}")
