# One-time setup for the nightly local-model list refresh. Run from the repo folder:
#   powershell -ExecutionPolicy Bypass -File local\setup.ps1
# Options: -At 00:05,02:05,04:05 (start times), -RunNow (run once right away), -Uninstall
param([string[]]$At = @('00:05', '02:05', '04:05'), [switch]$RunNow, [switch]$Uninstall)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent $here
$taskName = 'Solar dashboard lists'

if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed the '$taskName' task."
    return
}

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Ensure-Installed($command, $wingetId, $label) {
    if (Get-Command $command -ErrorAction SilentlyContinue) { Write-Host "OK  $label is installed"; return }
    Write-Host "... installing $label"
    winget install --id $wingetId -e --silent --accept-source-agreements --accept-package-agreements
    Refresh-Path
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "$label did not install. Install it by hand, open a new PowerShell window and run this again."
    }
}

Ensure-Installed git 'Git.Git' 'Git'
Ensure-Installed py 'Python.Python.3.12' 'Python'

$lms = Join-Path $env:USERPROFILE '.lmstudio\bin\lms.exe'
if (-not (Test-Path $lms)) { throw "LM Studio's lms tool was not found. Open LM Studio once, then run this again." }
Write-Host 'OK  LM Studio command line found'

$cfg = Get-Content (Join-Path $here 'sources.json') -Raw | ConvertFrom-Json
if ((& $lms ls | Out-String) -notmatch [regex]::Escape($cfg.lmstudio.model)) {
    throw "LM Studio does not have $($cfg.lmstudio.model). Download it, or change lmstudio.model in local\sources.json."
}
Write-Host "OK  model $($cfg.lmstudio.model) is downloaded"

Push-Location $repo
try {
    if (-not (git config user.name)) { git config user.name 'Parker (local lists)' }
    if (-not (git config user.email)) { git config user.email 'phallpdx@users.noreply.github.com' }
    git fetch --quiet origin main
    # Signs in to GitHub now (a browser window may open) so the nightly push never waits on a prompt.
    # --force like the nightly push: the branch is rewritten every run, so a plain push is refused.
    git push --dry-run --force origin "origin/main:refs/heads/$($cfg.push_branch)"
    if ($LASTEXITCODE -ne 0) { throw 'Git could not push to GitHub. Sign in when asked, then run this again.' }
    Write-Host 'OK  GitHub push access works'
} finally { Pop-Location }

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$here\run_daily.ps1`""
# Later runs mostly reuse cached answers, so they take minutes and fill in anything an earlier run missed.
$trigger = @($At | ForEach-Object { New-ScheduledTaskTrigger -Daily -At $_ })
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 4)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Force | Out-Null
Write-Host "OK  '$taskName' runs every night at $($At -join ', '). Logs go to $here\logs."

if ($RunNow) {
    Start-ScheduledTask -TaskName $taskName
    Write-Host "Started a run now. Watch $here\logs for progress."
}
