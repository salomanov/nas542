import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

ps_code = """
$p = '["\\x27]([A-Za-z0-9_]+)["\\x27]'
$text = 'os.environ.get("MY_VAR") and os.environ.get(\\'OTHER_VAR\\')'
$matches = [regex]::Matches($text, $p)
foreach ($m in $matches) {
    Write-Output "Found: $($m.Groups[1].Value)"
}
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_code], capture_output=True, text=True)
print("Output:", res.stdout)
print("Error:", res.stderr)
print("Exit code:", res.returncode)
