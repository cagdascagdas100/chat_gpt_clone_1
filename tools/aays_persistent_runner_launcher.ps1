param(
  [string]$Repo = 'C:\Users\cagda\Documents\GitHub\AAYS',
  [int]$Cycles = 24,
  [int]$SleepSeconds = 600
)

$ErrorActionPreference = 'Continue'
$LogDir = Join-Path $Repo 'docs\chatgpt_status\runner_outputs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Runner = Join-Path $Repo 'tools\aays_long_runner_cycle.ps1'
$OutLog = Join-Path $LogDir "aays-persistent-runner-$Stamp.out.log"
$ErrLog = Join-Path $LogDir "aays-persistent-runner-$Stamp.err.log"

if (!(Test-Path $Runner)) {
  Write-Host "MISSING_RUNNER=$Runner"
  exit 1
}

$Args = @(
  '-NoProfile',
  '-ExecutionPolicy', 'Bypass',
  '-File', $Runner,
  '-Cycles', $Cycles,
  '-SleepSeconds', $SleepSeconds
)

$proc = Start-Process -FilePath 'powershell.exe' -ArgumentList $Args -WorkingDirectory $Repo -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -WindowStyle Minimized -PassThru

$Status = @"
AAYS persistent runner launched
stamp=$Stamp
process_id=$($proc.Id)
repo=$Repo
cycles=$Cycles
sleep_seconds=$SleepSeconds
stdout_log=$OutLog
stderr_log=$ErrLog
expected_runtime_minutes=$([int](($Cycles * $SleepSeconds) / 60))
db_write=false
deploy=false
migration=false
fake_data=false
"@
$Status | Set-Content (Join-Path $LogDir 'aays-persistent-runner-launch-latest.txt') -Encoding UTF8
Write-Host $Status
