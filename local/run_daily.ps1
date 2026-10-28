# Nightly job: starts LM Studio's server with the model, refreshes the lists,
# then puts LM Studio back the way it found it. Registered by setup.ps1.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $here 'logs'
New-Item -ItemType Directory -Force $logDir | Out-Null
Get-ChildItem $logDir -Filter *.log | Where-Object LastWriteTime -lt (Get-Date).AddDays(-30) | Remove-Item
Start-Transcript -Path (Join-Path $logDir ('{0:yyyy-MM-dd}.log' -f (Get-Date))) -Append | Out-Null

# Pick up script and source fixes from GitHub. A run that can't update still
# runs with the code it has.
$repo = Split-Path -Parent $here
$env:GIT_TERMINAL_PROMPT = '0'  # never sit waiting for a sign-in nobody will see
try {
    $pull = Start-Process git -ArgumentList @('-C', "`"$repo`"", 'pull', '--ff-only', '--quiet') -Wait -PassThru -WindowStyle Hidden
    "git pull exit code: $($pull.ExitCode)"
} catch { "git pull failed: $_" }

$cfg = Get-Content (Join-Path $here 'sources.json') -Raw | ConvertFrom-Json
$model = $cfg.lmstudio.model

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
# The model doesn't quite fit on the 16 GB card at this context, and forcing it all on can freeze the PC,
# so part of it stays in system memory (gpu_offload is the share that goes on the GPU).
$loadArgs = @('load', $model, '--context-length', "$($cfg.lmstudio.context_length)", '-y')
if ($cfg.lmstudio.gpu_offload) { $loadArgs += @('--gpu', "$($cfg.lmstudio.gpu_offload)") }
if (-not $modelWasLoaded) { Lms $loadArgs }
"LM Studio server was running: $serverWasRunning; model was loaded: $([bool]$modelWasLoaded)"

# Python also gets its own console, and writes its progress straight to
# <date>-lists.log so it can be followed while the run is going.
$env:SOLAR_PARENT_PID = $PID  # Python stops itself if this script is ended
$env:SOLAR_LISTS_LOG = Join-Path $logDir ('{0:yyyy-MM-dd}-lists.log' -f (Get-Date))
$py = Get-Command py -ErrorAction SilentlyContinue
$pyArgs = @("`"$(Join-Path $here 'refresh_lists.py')`"") + $args
if ($py) { $exe = $py.Source; $pyArgs = @('-3') + $pyArgs } else { $exe = 'python' }
$out = [IO.Path]::GetTempFileName()
$proc = Start-Process $exe -ArgumentList $pyArgs -Wait -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $out -RedirectStandardError "$out.err"
Get-Content "$out.err" -ErrorAction SilentlyContinue  # errors that stopped Python, if any
Remove-Item $out, "$out.err" -ErrorAction SilentlyContinue
$code = $proc.ExitCode
"Lists progress is in $env:SOLAR_LISTS_LOG"

if (-not $modelWasLoaded) { Lms @('unload', $model) }
if (-not $serverWasRunning) { Lms @('server', 'stop') }
"Finished with exit code $code"
Stop-Transcript | Out-Null
exit $code
