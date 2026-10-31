import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_ps = """
$errors = $null
$tokens = $null
$ast = [System.Management.Automation.Language.Parser]::ParseInput(@'
$codePatterns = @(
    'os\.(?:environ\.get|getenv)\s*\(\s*["\x27]([A-Za-z0-9_]+)["\x27]'
)
'@, [ref]$tokens, [ref]$errors)

if ($errors) {
    foreach ($e in $errors) {
        Write-Output "ERR: $($e.Message) at char $($e.Extent.StartColumnNumber)"
    }
} else {
    Write-Output "Parsed successfully!"
}
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", test_ps], capture_output=True, text=True)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)
