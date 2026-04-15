import re
with open('users/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'def register\([^)]*\):(.+?)(?=def |\Z)', text, re.DOTALL)
if m:
    print(m.group(0))
else:
    print("Not found")

