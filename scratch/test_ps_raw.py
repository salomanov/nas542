import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Let's test PowerShell code where we define patterns using standard PowerShell here-string or escaping:
ps_code = r'''
$codePatterns = @(
    'os\.(?:environ\.get|getenv)\s*\(\s*["'']([A-Za-z0-9_]+)["'']',
    'os\.environ\s*\[\s*["'']([A-Za-z0-9_]+)["'']\s*\]',
    'process\.env\.([A-Za-z0-9_]+)',
    'process\.env\s*\[\s*["'']([A-Za-z0-9_]+)["'']\s*\]',
    'import\.meta\.env\.([A-Za-z0-9_]+)',
    'getenv\s*\(\s*["'']([A-Za-z0-9_]+)["'']\s*\)',
    '\$_ENV\s*\[\s*["'']([A-Za-z0-9_]+)["'']\s*\]',
    'Environment\.GetEnvironmentVariable\s*\(\s*["'']([A-Za-z0-9_]+)["'']',
    '\$env:([A-Za-z0-9_]+)'
)

$envFilePatterns = @(
    '(?m)^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=',
    '\$\{([A-Za-z0-9_]+)\}'
)

Write-Output "Patterns count: $($codePatterns.Count)"
foreach ($p in $codePatterns) {
    Write-Output "Pattern: $p"
}
'''

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_code], capture_output=True, text=True)
print("Stdout:\n", res.stdout)
print("Stderr:\n", res.stderr)
print("Exit code:", res.returncode)
