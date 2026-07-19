import os

for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith(('.yaml', '.yml', '.json', '.cfg', '.ini', '.toml')) and 'config' in f.lower():
            print(os.path.join(root, f))
