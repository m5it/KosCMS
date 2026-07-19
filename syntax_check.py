import ast
from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
content = p.read_text()

try:
    tree = ast.parse(content)
    
    # Find KosDBClient class and its methods
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "KosDBClient":
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            print(f"KosDBClient has {len(methods)} methods:")
            for m in methods:
                print(f"  - {m}")
            
            # Check for nested classes (like _ReconnectingConnection)
            nested = [n.name for n in node.body if isinstance(n, ast.ClassDef)]
            print(f"\nNested classes: {nested}")
    
    print("\nSyntax: OK")
except SyntaxError as e:
    print(f"Syntax error at line {e.lineno}: {e}")
