param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [int]$IntervalSeconds = 60,
  [int]$MaxLoops = 0
)

$ErrorActionPreference = 'Stop'
$runner = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1'
if (-not (Test-Path -LiteralPath $runner)) { throw "Canonical runner missing: $runner" }
$statusDir = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\status'
$heartbeatDir = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\heartbeat'
foreach ($d in @($statusDir,$heartbeatDir)) { if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null } }
$loop = 0
do {
  $loop++
  $now = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  [System.IO.File]::WriteAllText((Join-Path $heartbeatDir 'shared_runner_daemon_heartbeat_latest.txt'), "daemon_pid=$PID`nloop=$loop`nheartbeat_at=$now`n", [System.Text.UTF8Encoding]::new($false))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $runner -RepoRoot $RepoRoot -MaxTasks 1
  [System.IO.File]::WriteAllText((Join-Path $statusDir 'shared_runner_daemon_latest.json'), (@{daemon_pid=$PID; loop=$loop; last_run_at=$now; runner_exit_code=$LASTEXITCODE; CONTINUE_RUNNER_READY=$true; final_ready=$false} | ConvertTo-Json -Depth 10), [System.Text.UTF8Encoding]::new($false))
  if ($MaxLoops -gt 0 -and $loop -ge $MaxLoops) { break }
  Start-Sleep -Seconds $IntervalSeconds
} while ($true)