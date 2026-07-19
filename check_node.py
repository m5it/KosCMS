import shutil
for cmd in ['node', 'npm', 'npx', 'pnpm', 'yarn']:
    print(f"{cmd}: {shutil.which(cmd)}")
