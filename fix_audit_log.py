path = "webcms/models/system.py"
with open(path) as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'user_id = Column(String(36), nullable=True)' in line:
        lines[i] = '    user_id = Column(String(36), ForeignKey(\"users.id\"), nullable=True)\\n'
        break

with open(path, "w") as f:
    f.writelines(lines)

print("fixed")
