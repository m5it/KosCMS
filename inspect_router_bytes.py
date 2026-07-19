from pathlib import Path
p = Path("webcms/core/router.py")
b = p.read_bytes()
print(b[b.find(b"_compile_pattern"):b.find(b"_compile_pattern")+300])