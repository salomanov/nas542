import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ge_path = Path(r"C:\Users\Salomanov\.gemini\config\skills\project-guardian\scripts\gen-env.ps1")
raw = ge_path.read_bytes()
print("Raw line 32 bytes:", raw.split(b"\r\n")[31])
