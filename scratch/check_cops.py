import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

lines = Path(r"e:\Projects\NAS542\scripts\07-cops.sh").read_text(encoding="utf-8").splitlines()
for i, l in enumerate(lines, 1):
    if "a_new" in l:
        print(f"Line {i}: {l}")
