path = "webcms/admin/admin_api.py"
with open(path) as f:
    lines = f.readlines()
for i in range(1345, 1375):
    print(f"{i+1:4d}: {repr(lines[i])}")
