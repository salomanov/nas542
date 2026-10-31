import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_ps = r"""
$fileContent = Get-Content "E:\Projects\NAS542\scripts\00-secrets.env.example" -Raw -Encoding UTF8
$pattern = '(?m)^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*='
$matches = [regex]::Matches($fileContent, $pattern)
Write-Output "Matches count: $($matches.Count)"
foreach ($m in $matches) {
    Write-Output "Matched: $($m.Groups[1].Value)"
}
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", test_ps], capture_output=True, text=True)
print("Stdout:\n", res.stdout)
