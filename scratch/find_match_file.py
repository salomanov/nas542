import sys
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

test_ps = r"""
$ProjectPath = "e:\Projects\NAS542"
$excludeDirs = @(".git", ".backups", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", ".turbo")
$includeExts = @("*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.php", "*.cs", "*.sh", "*.env", "*.env.*", "*.*env*")

$files = Get-ChildItem -Path $ProjectPath -Recurse -File -Include $includeExts -ErrorAction SilentlyContinue | Where-Object {
    $full = $_.FullName
    $skip = $false
    foreach ($ex in $excludeDirs) {
        if ($full -like "*\$ex\*") { $skip = $true; break }
    }
    -not $skip
}

foreach ($f in $files) {
    $content = Get-Content $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ($content -match "a_new") {
        Write-Output "Matched file with a_new: $($f.FullName)"
    }
}
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", test_ps], capture_output=True, text=True)
print("Stdout:\n", res.stdout)
