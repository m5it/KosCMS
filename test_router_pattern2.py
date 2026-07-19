import sys; sys.path.insert(0, "webcms")
import re
path = "/admin/{filename:path}"
path = re.sub(r"\{(\w+):path\}", r"(?P<\1>.+)", path)
print("after sub1:", path)
path = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", path)
print("after sub2:", path)
path = re.sub(r"<(\w+):path>", r"(?P<\1>.+)", path)
print("after sub3:", path)
path = re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", path)
print("after sub4:", path)
print("compile:", re.compile(f"^{path}$"))