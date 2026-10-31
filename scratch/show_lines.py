import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ge_path = Path(r"C:\Users\Salomanov\.gemini\config\skills\project-guardian\scripts\gen-env.ps1")
lines = ge_path.read_text(encoding="utf-8").splitlines()
for i, l in enumerate(lines[:45], 1):
    print(f"{i:2d}: {l}")
