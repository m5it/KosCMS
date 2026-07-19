import os, json

for root, dirs, files in os.walk('.'):
    # skip venv/node_modules
    if any(p in root for p in ['node_modules','venv','.git','__pycache__']):
        continue
    for f in files:
        if f in ['TemplateManager.jsx','admin_api.py'] or f.endswith('TemplateManager.jsx'):
            print(os.path.join(root,f))
