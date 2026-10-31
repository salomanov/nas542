import subprocess
import sys

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
Write-Output "Files matched count: $($files.Count)"
foreach ($f in $files) {
    if ($f.Name -like "*secrets*") {
        Write-Output "File: $($f.FullName), Ext: $($f.Extension)"
    }
}
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", test_ps], capture_output=True, text=True)
print("Stdout:\n", res.stdout)
