$ErrorActionPreference = 'Stop'
$src = Join-Path $PSScriptRoot 'root_ca.crt'
try {
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($src)
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store('Root', 'LocalMachine')
    $store.Open('ReadWrite')
    $found = $store.Certificates | Where-Object { $_.Thumbprint -eq $cert.Thumbprint }
    if (-not $found) { $store.Add($cert); Write-Host "OK: added $($cert.Thumbprint) to LocalMachine\Root" -ForegroundColor Green }
    else { Write-Host "OK: already present $($cert.Thumbprint)" -ForegroundColor Green }
    $store.Close()
} catch {
    Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Right-click the .cmd and choose 'Run as administrator'." -ForegroundColor Yellow
}
