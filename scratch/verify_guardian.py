import sys
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

scripts_dir = Path(r"C:\Users\Salomanov\.gemini\config\skills\project-guardian\scripts")
ps1_files = list(scripts_dir.glob("*.ps1"))

print(f"Checking {len(ps1_files)} PowerShell scripts in {scripts_dir}:")
all_ok = True

for ps1 in ps1_files:
    raw = ps1.read_bytes()
    # Check double BOM
    if raw.startswith(b'\xef\xbb\xbf\xef\xbb\xbf'):
        print(f"❌ {ps1.name}: Double BOM found!")
        all_ok = False
    elif raw.startswith(b'\xef\xbb\xbf'):
        bom_status = "1 BOM"
    else:
        bom_status = "No BOM"

    # Syntax test via powershell parser
    cmd = [
        "powershell", "-NoProfile", "-Command",
        f"$errors = $null; $tokens = $null; [System.Management.Automation.Language.Parser]::ParseFile('{str(ps1)}', [ref]$tokens, [ref]$errors) | Out-Null; if ($errors.Count -gt 0) {{ $errors | ForEach-Object {{ Write-Error $_ }}; exit 1 }} else {{ exit 0 }}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ {ps1.name} ({bom_status}): Syntax Error!\n{res.stderr}")
        all_ok = False
    else:
        print(f"✅ {ps1.name} ({bom_status}): Syntax Valid")

if all_ok:
    print("\nAll PowerShell scripts parsed successfully with 0 errors!")
else:
    print("\nSome scripts failed verification.")
