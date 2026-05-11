$ErrorActionPreference = 'Continue'

# Assumption: This script is run manually from one existing PowerShell window.
# Assumption: It does not open new PowerShell windows.
# Assumption: It kills stale AAYS runner processes that use wrong bridge roots, then starts the clean foreground runner.

$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RepoUrl = 'https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
$ResumeLog = Join-Path $LogDir ('resume-single-window-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')

function Step([string]$Text) {
  $line = '[' + (Get-Date -Format 's') + '] ' + $Text
  Write-Host $line
  try {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    Add-Content -Encoding UTF8 -Path $ResumeLog -Value $line
  } catch {}
}

function GitSafe([string[]]$ArgsList) {
  try {
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $out = & git @ArgsList 2>&1 | Out-String
    $code = $LASTEXITCODE
    $ErrorActionPreference = $old
    if ($out) { Add-Content -Encoding UTF8 -Path $ResumeLog -Value $out }
    Step ('git ' + ($ArgsList -join ' ') + ' exit=' + $code)
    return $code
  } catch {
    Step ('git ' + ($ArgsList -join ' ') + ' exception=' + $_.Exception.Message)
    return 999
  }
}

Step 'RESUME_SINGLE_WINDOW_BEGIN'
Step "BridgeRoot=$BridgeRoot"
Step "ProjectRoot=$ProjectRoot"

if (-not (Test-Path $BridgeRoot)) {
  Step "Bridge root missing; cloning $RepoUrl"
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BridgeRoot) | Out-Null
  git clone $RepoUrl $BridgeRoot
}

Set-Location $BridgeRoot
New-Item -ItemType Directory -Force -Path `
  (Join-Path $BridgeRoot 'ai-tasks'), `
  (Join-Path $BridgeRoot 'ai-task-scripts'), `
  (Join-Path $BridgeRoot 'ai-results'), `
  (Join-Path $BridgeRoot 'ai-heartbeat'), `
  (Join-Path $BridgeRoot 'ai-runner-logs'), `
  (Join-Path $BridgeRoot 'ai-runner-state') | Out-Null

Step 'Git sync begin'
GitSafe @('fetch','origin','main') | Out-Null
GitSafe @('reset','--hard','origin/main') | Out-Null
Step 'Git sync done'

$env:AAYS_BRIDGE_ROOT = $BridgeRoot
$env:AAYS_PROJECT_ROOT = $ProjectRoot
$env:AAYS_ALLOWED_SCRIPT_DIR = 'ai-task-scripts'
$env:AAYS_RUNNER_POLL_SECONDS = '15'
$env:AAYS_TASK_TIMEOUT_SECONDS = '3600'

Step 'Stopping stale AAYS runner processes except current shell'
$currentPid = $PID
$parentPid = $null
try {
  $me = Get-CimInstance Win32_Process -Filter ("ProcessId = " + $currentPid)
  if ($me) { $parentPid = [int]$me.ParentProcessId }
} catch {}

$killed = 0
try {
  $procs = Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe' OR Name = 'pwsh.exe'" | Where-Object {
    $_.ProcessId -ne $currentPid -and
    ($null -eq $parentPid -or $_.ProcessId -ne $parentPid) -and
    (
      $_.CommandLine -like '*AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1*' -or
      $_.CommandLine -like '*AAYS_AUTOPILOT_RUNNER_V5.ps1*' -or
      $_.CommandLine -like '*AAYS_REMOTE_AUTOPILOT_V6.ps1*' -or
      $_.CommandLine -like '*AAYS_START_RUNNER_SINGLE_WINDOW.ps1*' -or
      $_.CommandLine -like '*AAYS_RESUME_SINGLE_WINDOW.ps1*'
    )
  }
  foreach ($p in $procs) {
    Step ('STOP_STALE_PID=' + $p.ProcessId + ' CMD=' + $p.CommandLine)
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    $killed++
  }
} catch {
  Step ('STALE_PROCESS_SCAN_WARNING=' + $_.Exception.Message)
}
Step ('STALE_PROCESSES_STOPPED=' + $killed)

$Heartbeat = Join-Path $BridgeRoot 'ai-heartbeat\resume-single-window.md'
@(
  '# AAYS Resume Single Window',
  '',
  'status: starting',
  ('checked_at: ' + (Get-Date -Format s)),
  ('bridge_root: ' + $BridgeRoot),
  ('project_root: ' + $ProjectRoot),
  ('resume_log: ' + $ResumeLog),
  'message: Starting clean foreground runner in this same PowerShell window.'
) | Set-Content -Encoding UTF8 -Path $Heartbeat

$Runner = Join-Path $BridgeRoot 'AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1'
if (-not (Test-Path $Runner)) {
  Step "RUNNER_MISSING=$Runner"
  throw "Runner missing: $Runner"
}

Step 'STARTING_FOREGROUND_RUNNER_NO_NEW_WINDOW'
Write-Host ''
Write-Host 'Runner bu pencerede basliyor. Bu pencereyi kapatma.' -ForegroundColor Green
Write-Host 'Yeni PowerShell penceresi acilmayacak.' -ForegroundColor Green
Write-Host ''

. $Runner
