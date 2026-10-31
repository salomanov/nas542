import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

lines = Path(r"C:\Users\Salomanov\.gemini\config\skills\project-guardian\scripts\gen-env.ps1").read_text(encoding="utf-8").splitlines()
for i in range(28, 55):
    print(f"{i+1:2d}: {lines[i]}")
