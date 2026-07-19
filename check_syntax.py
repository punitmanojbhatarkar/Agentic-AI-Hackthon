import ast
import sys

try:
    with open('agents/critic.py', 'r') as f:
        code = f.read()
    ast.parse(code)
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR at line {e.lineno}: {e.msg}")
    print(f"Text: {e.text}")
    sys.exit(1)
