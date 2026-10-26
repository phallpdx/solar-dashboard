# Nightly job: starts LM Studio's server with the model, refreshes the lists,
# then puts LM Studio back the way it found it. Registered by setup.ps1.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$cfg = Get-Content (Join-Path $here 'sources.json') -Raw | ConvertFrom-Json
$model = $cfg.lmstudio.model
$logDir = Join-Path $here 'logs'
New-Item -ItemType Directory -Force $logDir | Out-Null
Get-ChildItem $logDir -Filter *.log | Where-Object LastWriteTime -lt (Get-Date).AddDays(-30) | Remove-Item
Start-Transcript -Path (Join-Path $logDir ('{0:yyyy-MM-dd}.log' -f (Get-Date))) -Append | Out-Null

# Windows PowerShell's transcript misses output from programs like python
# unless it is passed through as text, so it goes through Log.
function Log { process { "$_" } }
$env:PYTHONUNBUFFERED = '1'
$env:PYTHONIOENCODING = 'utf-8'

$lms = Join-Path $env:USERPROFILE '.lmstudio\bin\lms.exe'
if (-not (Test-Path $lms)) { $lms = (Get-Command lms -ErrorAction Stop).Source }

# lms runs in its own hidden console: inside the task's console it can send a
# Ctrl+C that ends this script.
function Lms([string[]]$arguments) {
    $out = [IO.Path]::GetTempFileName()
    Start-Process $lms -ArgumentList $arguments -Wait -WindowStyle Hidden `
        -RedirectStandardOutput $out -RedirectStandardError "$out.err" | Out-Null
    Get-Content $out, "$out.err" -ErrorAction SilentlyContinue
    Remove-Item $out, "$out.err" -ErrorAction SilentlyContinue
}

function Loaded-Models {
    try { (Invoke-RestMethod "$($cfg.lmstudio.url)/v1/models" -TimeoutSec 10).data.id } catch { $null }
}

$before = Loaded-Models
$serverWasRunning = $null -ne $before
if (-not $serverWasRunning) { Lms @('server', 'start'); Start-Sleep 5 }
$modelWasLoaded = @(Loaded-Models) -match [regex]::Escape($model.Split('/')[-1])
if (-not $modelWasLoaded) { Lms @('load', $model, '--context-length', "$($cfg.lmstudio.context_length)", '-y') }
"LM Studio server was running: $serverWasRunning; model was loaded: $([bool]$modelWasLoaded)"

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) { & $py.Source -3 (Join-Path $here 'refresh_lists.py') @args 2>&1 | Log }
else { & python (Join-Path $here 'refresh_lists.py') @args 2>&1 | Log }
$code = $LASTEXITCODE

if (-not $modelWasLoaded) { Lms @('unload', $model) }
if (-not $serverWasRunning) { Lms @('server', 'stop') }
"Finished with exit code $code"
Stop-Transcript | Out-Null
exit $code
