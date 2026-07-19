path = "webcms/admin/admin_api.py"
with open(path) as f:
    lines = f.readlines()

for i in range(475, 495):
    print(f"{i+1:4d}: {lines[i].rstrip()}")

print("---")
for i in range(809, 860):
    print(f"{i+1:4d}: {lines[i].rstrip()}")

print("---")
for i in range(1473, 1515):
    print(f"{i+1:4d}: {lines[i].rstrip()}")
