import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_ps = r"""
$f = Get-ChildItem -Path "e:\Projects\NAS542" -Recurse -File -Include @("*.py", "*.sh", "*.example", "*.*env*")
Write-Output "Count: $($f.Count)"
$target = $f | Where-Object { $_.Name -like "*00-secrets*" }
Write-Output "Found: $($target.FullName)"
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", test_ps], capture_output=True, text=True)
print("Stdout:\n", res.stdout)
