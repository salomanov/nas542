import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

guardian_dir = Path(r"C:\Users\Salomanov\.gemini\config\skills\project-guardian\scripts")
target_files = ["install-skill.ps1", "rollback.ps1", "record-failure.ps1"]

for fname in target_files:
    fpath = guardian_dir / fname
    if not fpath.exists():
        print(f"File not found: {fpath}")
        continue
    raw = fpath.read_bytes()
    boms_found = 0
    while raw.startswith(b'\xef\xbb\xbf'):
        boms_found += 1
        raw = raw[3:]
    print(f"{fname}: found {boms_found} BOM(s), new length {len(raw)} bytes")
    # Write back clean UTF-8 with exactly single BOM (or no BOM; in PS 5.1/7 UTF-8 with BOM or UTF-8 no BOM is fine)
    # Standard PowerShell UTF-8 with BOM is b'\xef\xbb\xbf' + raw
    fpath.write_bytes(b'\xef\xbb\xbf' + raw)
    print(f"Fixed {fname} with exactly 1 BOM.")
