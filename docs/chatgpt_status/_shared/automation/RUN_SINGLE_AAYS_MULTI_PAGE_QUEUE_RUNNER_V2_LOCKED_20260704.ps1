param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$RunnerScript = '',
  [int]$StaleMinutes = 20
)
$ErrorActionPreference = 'Stop'
function N { (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function D($p){ if($p -and !(Test-Path -LiteralPath $p)){ New-Item -ItemType Directory -Force -Path $p | Out-Null } }
function W($p,$c){ D (Split-Path -Parent $p); [IO.File]::WriteAllText($p,$c,[Text.UTF8Encoding]::new($false)) }
function J($o){ $o|ConvertTo-Json -Depth 20 }
$shared = Join-Path $RepoRoot 'docs\chatgpt_status\_shared'
$lockDir = Join-Path $shared 'runner_lock'
$statusDir = Join-Path $shared 'status'
$reportDir = Join-Path $shared 'reports'
$heartbeatDir = Join-Path $shared 'heartbeat'
foreach($d in @($lockDir,$statusDir,$reportDir,$heartbeatDir)){ D $d }
$lockPath = Join-Path $lockDir 'MULTI_PAGE.lock'
$hbPath = Join-Path $heartbeatDir 'MULTI_PAGE_heartbeat_latest.json'
if(!$RunnerScript){ $RunnerScript = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V2_20260704.ps1' }
if(Test-Path -LiteralPath $lockPath){
  $raw = Get-Content -LiteralPath $lockPath -Raw -ErrorAction SilentlyContinue
  $stale = $true
  try { $lock = $raw | ConvertFrom-Json; if($lock.heartbeat_path -and (Test-Path -LiteralPath $lock.heartbeat_path)){ $age = (Get-Date) - (Get-Item -LiteralPath $lock.heartbeat_path).LastWriteTime; $stale = ($age.TotalMinutes -gt $StaleMinutes) } } catch {}
  $payload = [ordered]@{ status = if($stale){'STALE_LOCK_DETECTED'}else{'RUNNER_LOCK_ACTIVE'}; stale=$stale; checked_at=N; final_ready=$false; blocker=if($stale){'STALE_LOCK_REPORTED_NOT_DELETED'}else{'SINGLE_RUNNER_ALREADY_ACTIVE'}; lock_path=$lockPath }
  W (Join-Path $statusDir 'MULTI_PAGE_latest_status.json') (J $payload)
  W (Join-Path $reportDir ('MULTI_PAGE_lock_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.json')) (J $payload)
  Write-Output (J $payload)
  exit 0
}
$lockPayload = [ordered]@{ pid=$PID; started_at=N; repo_root=$RepoRoot; heartbeat_path=$hbPath; lock_path=$lockPath; runner='RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V2_LOCKED_20260704' }
W $lockPath (J $lockPayload)
W $hbPath (J $lockPayload)
try {
  if(!(Test-Path -LiteralPath $RunnerScript)){ throw 'RUNNER_SCRIPT_MISSING: ' + $RunnerScript }
  & powershell -NoProfile -ExecutionPolicy Bypass -File $RunnerScript
  exit $LASTEXITCODE
} finally {
  if(Test-Path -LiteralPath $lockPath){
    try { $current = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json; if([int]$current.pid -eq [int]$PID){ Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue } } catch {}
  }
}
