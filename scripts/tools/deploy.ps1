# Заливает scripts/, configs/ и tls/ на NAS и запускает скрипт под sudo.
#
#   .\scripts\tools\deploy.ps1                          # install-all.sh
#   .\scripts\tools\deploy.ps1 -Script 03-syncthing.sh
#   .\scripts\tools\deploy.ps1 -Script tools/healthcheck.sh
#
# Параметры подключения берутся из scripts\00-secrets.env (NAS_LAN_IP, SSH_PORT,
# NAS_ADMIN_USER, NAS_ADMIN_PASS) или из аргументов.

param(
    [string]$Script = 'install-all.sh',
    [string]$ScriptArgs = '',
    [string]$NasHost,
    [int]$SshPort = 0,
    [string]$User,
    [string]$Pass,
    [switch]$NoUpload,
    [string]$WinScp = 'C:\Program Files (x86)\WinSCP\WinSCP.com'
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$scriptsDir = Split-Path $PSScriptRoot -Parent          # ...\scripts
$root       = Split-Path $scriptsDir -Parent             # корень репозитория
$secrets    = Join-Path $scriptsDir '00-secrets.env'

if (Test-Path $secrets) {
    Get-Content $secrets | ForEach-Object {
        if ($_ -match '^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$') {
            Set-Variable -Name $Matches[1] -Value $Matches[2] -Scope Script -ErrorAction SilentlyContinue
        }
    }
}

if (-not $NasHost) { $NasHost = $NAS_LAN_IP }
if (-not $SshPort) { $SshPort = if ($SSH_PORT) { [int]$SSH_PORT } else { 22 } }
if (-not $User)    { $User    = if ($NAS_ADMIN_USER) { $NAS_ADMIN_USER } else { 'admin' } }
if (-not $Pass)    { $Pass    = $NAS_ADMIN_PASS }

if (-not $NasHost) { throw "Не задан NAS_LAN_IP (scripts\00-secrets.env или -NasHost)." }
if (-not $Pass)    { throw "Не задан NAS_ADMIN_PASS (scripts\00-secrets.env или -Pass)." }

$encUser = [uri]::EscapeDataString($User)
$encPass = [uri]::EscapeDataString($Pass)

$lines = @(
    'option batch abort',
    'option confirm off',
    "open sftp://$encUser`:$encPass@$NasHost`:$SshPort/ -hostkey=* -timeout=30"
)

if (-not $NoUpload) {
    # удалённые каталоги должны существовать до synchronize
    $lines += 'call mkdir -p /tmp/nas542/scripts /tmp/nas542/configs /tmp/nas542/tls'
    $lines += "synchronize remote `"$root\scripts`" /tmp/nas542/scripts"
    $lines += "synchronize remote `"$root\configs`" /tmp/nas542/configs"
    if (Test-Path (Join-Path $root 'tls')) {
        $lines += "synchronize remote `"$root\tls`" /tmp/nas542/tls"
    }
}

$run = "echo $Pass | sudo -S sh /tmp/nas542/scripts/$Script"
if ($ScriptArgs) { $run += " $ScriptArgs" }
$lines += "call $run 2>&1"
$lines += 'exit'

$tmp = Join-Path $env:TEMP 'nas542-deploy.txt'
[System.IO.File]::WriteAllText($tmp, ($lines -join "`n"), (New-Object System.Text.UTF8Encoding($false)))

Write-Host "==> $NasHost`:$SshPort  /tmp/nas542/scripts/$Script $ScriptArgs" -ForegroundColor Cyan
$out = & $WinScp /log=nul /script=$tmp 2>&1
$code = $LASTEXITCODE
# прячем служебную шапку и сам пароль
$out |
    Where-Object { $_ -notmatch '^\s*(batch|confirm)\s' -and $_ -notmatch [regex]::Escape($Pass) } |
    Out-String

if ($code -ne 0) { Write-Host "WinSCP exit code: $code" -ForegroundColor Red }
