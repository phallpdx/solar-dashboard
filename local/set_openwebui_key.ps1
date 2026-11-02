# Saves an Open WebUI API key for the nightly job, so it can run web searches through
# Open WebUI (http://localhost:3000). Make the key in Open WebUI: Settings > Account > API Keys
# (an admin has to turn on "Enable API Keys" in Admin Panel > Settings > General first).
# The key is encrypted for this Windows account only and never leaves the PC.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$file = Join-Path $here 'openwebui_key.dat'
$cfg = Get-Content (Join-Path $here 'sources.json') -Raw | ConvertFrom-Json

$secure = Read-Host 'Paste the Open WebUI API key' -AsSecureString
$key = [Net.NetworkCredential]::new('', $secure).Password.Trim()
if (-not $key) { Write-Host 'No key entered; nothing saved.'; exit 1 }

try {
    Invoke-RestMethod "$($cfg.openwebui.url)/api/models" -Headers @{ Authorization = "Bearer $key" } -TimeoutSec 20 | Out-Null
} catch {
    Write-Host "Open WebUI didn't accept that key ($($_.Exception.Message)). Nothing saved."
    exit 1
}
ConvertTo-SecureString $key -AsPlainText -Force | ConvertFrom-SecureString | Set-Content $file
Write-Host "Saved. The nightly job will use it from now on."
