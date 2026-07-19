path = "webcms/templates/engine.py"
with open(path) as f:
    lines = f.readlines()

for i in range(378, 445):
    print(f"{i+1:4d}: {lines[i].rstrip()}")
