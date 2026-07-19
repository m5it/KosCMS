import subprocess
result = subprocess.run(['git', 'diff', '--stat'], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
