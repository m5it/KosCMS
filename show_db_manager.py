path = "webcms/database/connection.py"
with open(path) as f:
    lines = f.readlines()

for i in range(17, 90):
    print(f"{i+1:4d}: {lines[i].rstrip()}")
