# Nightly job: starts LM Studio's server with the model, refreshes the lists,
# then puts LM Studio back the way it found it. Registered by setup.ps1.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$cfg = Get-Content (Join-Path $here 'sources.json') -Raw | ConvertFrom-Json
$model = $cfg.lmstudio.model
$logDir = Join-Path $here 'logs'
New-Item -ItemType Directory -Force $logDir | Out-Null
Get-ChildItem $logDir -Filter *.log | Where-Object LastWriteTime -lt (Get-Date).AddDays(-30) | Remove-Item
Start-Transcript -Path (Join-Path $logDir ('{0:yyyy-MM-dd}.log' -f (Get-Date))) -Append | Out-Null

$lms = Join-Path $env:USERPROFILE '.lmstudio\bin\lms.exe'
if (-not (Test-Path $lms)) { $lms = (Get-Command lms -ErrorAction Stop).Source }

$serverWasRunning = (& $lms server status 2>&1 | Out-String) -notmatch 'not running'
if (-not $serverWasRunning) { & $lms server start }
$modelWasLoaded = (& $lms ps 2>&1 | Out-String) -match [regex]::Escape($model)
if (-not $modelWasLoaded) { & $lms load $model --context-length $cfg.lmstudio.context_length -y }

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) { & $py.Source -3 (Join-Path $here 'refresh_lists.py') @args }
else { & python (Join-Path $here 'refresh_lists.py') @args }
$code = $LASTEXITCODE

if (-not $modelWasLoaded) { & $lms unload $model }
if (-not $serverWasRunning) { & $lms server stop }
Stop-Transcript | Out-Null
exit $code
