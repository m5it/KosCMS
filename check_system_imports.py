path = "webcms/models/system.py"
with open(path) as f:
    content = f.read()
print('ForeignKey' in content)
print(content[:200])
