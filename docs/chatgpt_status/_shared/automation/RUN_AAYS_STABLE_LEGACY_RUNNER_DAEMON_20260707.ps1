[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738",
  [string]$RepoFullName = "cagdascagdas100/chat_gpt_clone_1",
  [string]$MainBranch = "codex/aays-single-runner-v5-20260706",
  [string]$WorkRoot = "C:\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES",
  [int]$IntervalSeconds = 60,
  [int]$MaxTasks = 1,
  [int]$StaleMinutes = 20,
  [int]$MaxLoops = 0,
  [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$sharedRoot = Join-Path $RepoRoot "docs\chatgpt_status\_shared"
$automationRoot = Join-Path $sharedRoot "automation"
$runner = Join-Path $automationRoot "RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1"
$statusDir = Join-Path $sharedRoot "status"
$heartbeatDir = Join-Path $sharedRoot "heartbeat"
$lockDir = Join-Path $sharedRoot "locks"
foreach ($dir in @($statusDir,$heartbeatDir,$lockDir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
$lockPath = Join-Path $lockDir "single_runner.lock"
$statusPath = Join-Path $statusDir "stable_runner_daemon_latest.json"
$bootstrapPath = Join-Path $statusDir "runner_bootstrap_latest.json"
$heartbeatPath = Join-Path $heartbeatDir "stable_runner_daemon_heartbeat_latest.json"

function Now-Utc { (Get-Date).ToUniversalTime().ToString("o") }
function Write-Json($Path, $Payload) { $Payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Path -Encoding UTF8 }
function Read-Json($Path) { try { if (Test-Path -LiteralPath $Path) { return Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json } } catch {}; return $null }

if (Test-Path -LiteralPath $lockPath) {
  $lock = Read-Json $lockPath
  $existingPid = if ($lock -and $lock.pid) { [int]$lock.pid } else { $null }
  $existing = if ($existingPid) { Get-Process -Id $existingPid -ErrorAction SilentlyContinue } else { $null }
  $age = ((Get-Date) - (Get-Item -LiteralPath $lockPath).LastWriteTime).TotalMinutes
  if ($existing -and $age -lt $StaleMinutes) {
    $payload = [ordered]@{ checked_at=Now-Utc; status="already_running"; active_pid=$existingPid; lock_path="docs/chatgpt_status/_shared/locks/single_runner.lock"; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
    Write-Json $statusPath $payload
    Write-Json $bootstrapPath ([ordered]@{
      updated_at=Now-Utc
      repo_root=$RepoRoot
      repo_full_name=$RepoFullName
      runner_branch=$MainBranch
      runner_status='runner_active'
      runner_engine='stable_legacy_worktree_runner_20260707'
      scan_runner='RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707'
      runner_pid=$existingPid
      runner_lock_active=(Test-Path -LiteralPath $lockPath)
      lock_file='docs/chatgpt_status/_shared/locks/single_runner.lock'
      panel_index='docs/chatgpt_status/_shared/panel/page_status_index_latest.json'
      CONTINUE_RUNNER_READY=$true
      final_ready=$false
      product_final_ready=$false
      fake_data=$false
      db_write=$false
      migration=$false
      production_deploy=$false
    })
    Write-Output ($payload | ConvertTo-Json -Depth 20)
    exit 0
  }
  Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
}

$lockPayload = [ordered]@{ pid=$PID; runner="RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707"; scan_runner="RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707"; repo_root=$RepoRoot; branch=$MainBranch; started_at=Now-Utc; updated_at=Now-Utc; final_ready=$false }
Write-Json $lockPath $lockPayload
Start-Sleep -Seconds 5
$loop = 0
try {
  do {
    $loop++
    $started = Now-Utc
    Write-Json $heartbeatPath ([ordered]@{ daemon_pid=$PID; loop=$loop; heartbeat_at=$started; runner_active=$true; scan_runner="RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707"; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false })
    $args = @("-RepoRoot", $RepoRoot, "-RepoFullName", $RepoFullName, "-MainBranch", $MainBranch, "-WorkRoot", $WorkRoot, "-MaxTasks", "$MaxTasks", "-StaleMinutes", "$StaleMinutes")
    if ($NoPush) { $args += "-NoPush" }
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $runner @args 2>&1
    $code = $LASTEXITCODE
    $tail = ($out | Out-String).Trim()
    if ($tail.Length -gt 6000) { $tail = $tail.Substring($tail.Length - 6000) }
    $payload = [ordered]@{ checked_at=Now-Utc; daemon_pid=$PID; loop=$loop; status="runner_loop_completed"; scan_runner="RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707"; runner_exit_code=$code; runner_output_tail=$tail; CONTINUE_RUNNER_READY=$true; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
    Write-Json $statusPath $payload
    Write-Json $bootstrapPath ([ordered]@{
      updated_at=Now-Utc
      repo_root=$RepoRoot
      repo_full_name=$RepoFullName
      runner_branch=$MainBranch
      runner_status='runner_active'
      runner_engine='stable_legacy_worktree_runner_20260707'
      scan_runner='RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707'
      runner_pid=$PID
      runner_lock_active=(Test-Path -LiteralPath $lockPath)
      lock_file='docs/chatgpt_status/_shared/locks/single_runner.lock'
      panel_index='docs/chatgpt_status/_shared/panel/page_status_index_latest.json'
      CONTINUE_RUNNER_READY=$true
      final_ready=$false
      product_final_ready=$false
      fake_data=$false
      db_write=$false
      migration=$false
      production_deploy=$false
    })
    if ($MaxLoops -gt 0 -and $loop -ge $MaxLoops) { break }
    Start-Sleep -Seconds $IntervalSeconds
  } while ($true)
} finally {
  $current = Read-Json $lockPath
  if ($current -and [int]$current.pid -eq [int]$PID) { Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue }
}
