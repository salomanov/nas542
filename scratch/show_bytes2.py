import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ge_path = Path(r"C:\Users\Salomanov\.gemini\config\skills\project-guardian\scripts\gen-env.ps1")
raw = ge_path.read_bytes()
lines = raw.split(b"\n")
print(f"Total lines with \\n: {len(lines)}")
for i in range(min(40, len(lines))):
    print(f"{i+1:2d}: {lines[i]}")
