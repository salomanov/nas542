import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ge_path = Path(r"C:\Users\Salomanov\.gemini\config\skills\project-guardian\scripts\gen-env.ps1")
lines = ge_path.read_text(encoding="utf-8").splitlines()
line32 = lines[31] # 0-indexed
print("Line 32:", repr(line32))
for idx, ch in enumerate(line32):
    print(f"{idx+1}: {ch}")
