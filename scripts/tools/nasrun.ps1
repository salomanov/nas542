# Выполнить произвольную команду на NAS под sudo через WinSCP.
#
#   .\scripts\tools\nasrun.ps1 "ls -la /opt/etc/init.d"
#   .\scripts\tools\nasrun.ps1 "cat /i-data/45f1aca1/Apps/logs/syncthing.log | tail -20"
#
# Параметры подключения — из scripts\00-secrets.env.

param(
    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)][string[]]$Cmd,
    [string]$WinScp = 'C:\Program Files (x86)\WinSCP\WinSCP.com'
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$scriptsDir = Split-Path $PSScriptRoot -Parent
$secrets    = Join-Path $scriptsDir '00-secrets.env'

$NAS_LAN_IP = $null; $SSH_PORT = $null; $NAS_ADMIN_USER = $null; $NAS_ADMIN_PASS = $null
if (Test-Path $secrets) {
    Get-Content $secrets | ForEach-Object {
        if ($_ -match '^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$') {
            Set-Variable -Name $Matches[1] -Value $Matches[2] -Scope Script
        }
    }
}

if (-not $NAS_LAN_IP)   { throw "Не задан NAS_LAN_IP в scripts\00-secrets.env" }
if (-not $NAS_ADMIN_PASS) { throw "Не задан NAS_ADMIN_PASS в scripts\00-secrets.env" }
$port = if ($SSH_PORT) { [int]$SSH_PORT } else { 22 }

$encUser = [uri]::EscapeDataString($NAS_ADMIN_USER)
$encPass = [uri]::EscapeDataString($NAS_ADMIN_PASS)
$line    = ($Cmd -join ' ')

$script = @"
option batch abort
option confirm off
open sftp://$encUser`:$encPass@$NAS_LAN_IP`:$port/ -hostkey=* -timeout=30
call echo $NAS_ADMIN_PASS | sudo -S $line 2>&1
exit
"@

$tmp = Join-Path $env:TEMP 'nasrun.txt'
[System.IO.File]::WriteAllText($tmp, $script, (New-Object System.Text.UTF8Encoding($false)))

& $WinScp /log=nul /script=$tmp 2>&1 |
    Where-Object { $_ -notmatch '\p{IsCyrillic}' } |
    Out-String
