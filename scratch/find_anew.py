import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

for f in Path(r"e:\Projects\NAS542").rglob("*"):
    if f.is_file() and (".git" not in f.parts and ".backups" not in f.parts):
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if "a_new" in content:
                print(f"File with a_new: {f}")
        except:
            pass
