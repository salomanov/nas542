import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

f = Path(r"e:\Projects\NAS542\scripts\00-secrets.env.example")
if f.exists():
    print(f.read_text(encoding='utf-8'))
else:
    print("File does not exist")
