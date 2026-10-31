import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_ps = r"""
$p1 = (Get-ChildItem -Path "e:\Projects\NAS542" -Recurse -File -Include "*.sh").Count
$p2 = (Get-ChildItem -Path "e:\Projects\NAS542\*" -Recurse -File -Include "*.sh").Count
$p3 = (Get-ChildItem -Path "e:\Projects\NAS542" -Recurse -File | Where-Object { $_.Extension -eq ".sh" }).Count
Write-Output "Include without star: $p1"
Write-Output "Include with star: $p2"
Write-Output "Where-Object: $p3"
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", test_ps], capture_output=True, text=True)
print("Stdout:\n", res.stdout)
