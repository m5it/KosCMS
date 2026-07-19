path = "webcms/admin/admin_api.py"
with open(path) as f:
    lines = f.readlines()

for i in range(1468, 1505):
    print(f"{i+1:4d}: {lines[i].rstrip()}")
