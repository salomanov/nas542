import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

content = Path(r"e:\Projects\NAS542\scripts\07-cops.sh").read_text(encoding="utf-8")

patterns = [
    r'os\.(?:environ\.get|getenv)\s*\(\s*["\']([A-Za-z0-9_]+)["\']',
    r'os\.environ\s*\[\s*["\']([A-Za-z0-9_]+)["\']\s*\]',
    r'process\.env\.([A-Za-z0-9_]+)',
    r'process\.env\s*\[\s*["\']([A-Za-z0-9_]+)["\']\s*\]',
    r'import\.meta\.env\.([A-Za-z0-9_]+)',
    r'getenv\s*\(\s*["\']([A-Za-z0-9_]+)["\']\s*\)',
    r'\$_ENV\s*\[\s*["\']([A-Za-z0-9_]+)["\']\s*\]',
    r'Environment\.GetEnvironmentVariable\s*\(\s*["\']([A-Za-z0-9_]+)["\']',
    r'\$env:([A-Za-z0-9_]+)',
    r'(?m)^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)\s*='
]

for idx, p in enumerate(patterns):
    matches = re.findall(p, content)
    if matches:
        print(f"Pattern {idx} matched in 07-cops.sh: {matches}")
