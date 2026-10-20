# Публикация библиотеки Calibre с ПК на NAS (SFTP).
#
#   .\scripts\tools\publish-calibre.ps1
#   .\scripts\tools\publish-calibre.ps1 -LocalLibrary "D:\Books\Calibre Library"
#   .\scripts\tools\publish-calibre.ps1 -NoDelete      # не удалять книги на NAS
#
# Что делает:
#   1. снимает консистентный снимок metadata.db (sqlite backup API) - можно
#      запускать даже при открытом Calibre;
#   2. синхронизирует папку библиотеки на NAS (только изменения, удаления тоже);
#   3. заливает снимок базы последним, чтобы она никогда не ссылалась на
#      ещё не загруженные файлы;
#   4. сверяет число книг на NAS с локальным.
#
# Параметры берутся из scripts\00-secrets.env (NAS_WAN_IP, SSH_PORT,
# NAS_ADMIN_USER, NAS_ADMIN_PASS).

param(
    [string]$LocalLibrary = '',   # по умолчанию берётся текущая библиотека Calibre
    [string]$RemoteDir = '/i-data/45f1aca1/Apps/calibre',
    [string]$NasHost,
    [int]$SshPort = 0,
    [string]$User,
    [string]$Pass,
    [int]$WebPort = 34501,
    [switch]$NoDelete,
    [string]$WinScp = 'C:\Program Files (x86)\WinSCP\WinSCP.com'
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$scriptsDir = Split-Path $PSScriptRoot -Parent
$secrets = Join-Path $scriptsDir '00-secrets.env'

if (Test-Path $secrets) {
    Get-Content $secrets | ForEach-Object {
        if ($_ -match '^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$') {
            Set-Variable -Name $Matches[1] -Value $Matches[2] -Scope Script -ErrorAction SilentlyContinue
        }
    }
}

# Библиотека по умолчанию - та, что открыта в Calibre (global.py.json).
if (-not $LocalLibrary) {
    $cfg = Join-Path $env:APPDATA 'calibre\global.py.json'
    if (Test-Path $cfg) {
        try { $LocalLibrary = (Get-Content $cfg -Raw -Encoding utf8 | ConvertFrom-Json).library_path } catch { }
    }
    if (-not $LocalLibrary) { $LocalLibrary = Join-Path $env:USERPROFILE 'Calibre Library' }
}

if (-not $NasHost) { $NasHost = if ($NAS_WAN_IP) { $NAS_WAN_IP } else { $NAS_LAN_IP } }
if (-not $SshPort) { $SshPort = if ($SSH_PORT) { [int]$SSH_PORT } else { 22 } }
if (-not $User)    { $User    = if ($NAS_ADMIN_USER) { $NAS_ADMIN_USER } else { 'admin' } }
if (-not $Pass)    { $Pass    = $NAS_ADMIN_PASS }

if (-not $NasHost) { throw "Нет NAS_WAN_IP (scripts\00-secrets.env или -NasHost)." }
if (-not $Pass)    { throw "Нет NAS_ADMIN_PASS (scripts\00-secrets.env или -Pass)." }
if (-not (Test-Path (Join-Path $LocalLibrary 'metadata.db'))) {
    throw "Не найдена библиотека Calibre: $LocalLibrary\metadata.db"
}

$logDir = Join-Path $env:LOCALAPPDATA 'nas542'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logFile = Join-Path $logDir 'publish.log'

function Log([string]$Text) {
    $line = "{0:yyyy-MM-dd HH:mm:ss}  {1}" -f (Get-Date), $Text
    Write-Host $Text
    Add-Content -Path $logFile -Value $line -Encoding utf8
}

$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) { throw 'Не найден python для снимка metadata.db.' }

# --- 1. консистентный снимок базы -------------------------------------------
$snap = Join-Path $env:TEMP 'calibre-metadata-publish.db'
$countFile = Join-Path $env:TEMP 'calibre-count.txt'
$pyFile = Join-Path $env:TEMP 'calibre-publish-snapshot.py'

@'
import sqlite3, sys
src, dst, count_file = sys.argv[1], sys.argv[2], sys.argv[3]
s = sqlite3.connect(f'file:{src}?mode=ro', uri=True)
d = sqlite3.connect(dst)
s.backup(d)
count = s.execute('select count(*) from books').fetchone()[0]
with open(count_file, 'w', encoding='utf-8') as fh:
    fh.write(str(count))
d.close(); s.close()
'@ | Set-Content -Path $pyFile -Encoding utf8

& $python.Source $pyFile (Join-Path $LocalLibrary 'metadata.db') $snap $countFile
if ($LASTEXITCODE -ne 0) { throw 'Не удалось снять снимок metadata.db.' }
$localCount = [int](Get-Content $countFile -Raw).Trim()

Log "==> $NasHost`:$SshPort  $LocalLibrary  ($localCount книг)"

# --- 2-3. синхронизация + база ----------------------------------------------
$encUser = [uri]::EscapeDataString($User)
$encPass = [uri]::EscapeDataString($Pass)
$delete = if ($NoDelete) { '' } else { ' -delete' }
$mask = '-filemask="|.thumbs/;inbox/;*.db-journal;*.db-wal;*.db-shm;metadata.db"'

$lines = @(
    'option batch abort',
    'option confirm off',
    "open sftp://$encUser`:$encPass@$NasHost`:$SshPort/ -hostkey=* -timeout=30",
    "synchronize remote `"$LocalLibrary`" $RemoteDir$delete $mask",
    "put `"$snap`" $RemoteDir/metadata.db",
    'exit'
)

$tmp = Join-Path $env:TEMP 'nas542-publish.txt'
[System.IO.File]::WriteAllText($tmp, ($lines -join "`n"), (New-Object System.Text.UTF8Encoding($false)))

$out = & $WinScp /log=nul /script=$tmp 2>&1
$code = $LASTEXITCODE
$errors = $out | Where-Object { $_ -match 'Error|error|Cannot|denied|failed' }
if ($errors) { Log ($errors -join "`n") }
if ($code -ne 0) { throw "WinSCP завершился с кодом $code (см. $logFile)." }

# --- 4. проверка -------------------------------------------------------------
if ($WebPort -gt 0) {
    Start-Sleep -Seconds 2
    $url = "https://$NasHost`:$WebPort/apps/cops/ui/api.php?action=list&limit=1"
    try {
        $json = & curl.exe -k -s --max-time 30 -u "$($User):$($Pass)" $url
        if ($json -match '"total"\s*:\s*(\d+)') {
            $remoteCount = [int]$Matches[1]
            if ($remoteCount -eq $localCount) {
                Log "OK: на NAS $remoteCount книг, как и локально."
            } else {
                Log "ВНИМАНИЕ: на NAS $remoteCount книг, локально $localCount."
            }
        } else {
            Log "Проверка пропущена: не разобрал ответ API."
        }
    } catch {
        Log "Проверка пропущена: $($_.Exception.Message)"
    }
}

Log 'Готово.'
