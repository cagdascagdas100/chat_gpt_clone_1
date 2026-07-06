param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1',
  [string]$MainBranch = 'main',
  [int]$MaxTasks = 1,
  [int]$StaleMinutes = 20
)

$ErrorActionPreference = 'Stop'
$repoFull = [System.IO.Path]::GetFullPath($RepoRoot)
if (-not $repoFull.StartsWith('F:\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "BLOCKED_WRONG_REPO_ROOT: $repoFull"
}
if (-not (Test-Path -LiteralPath $repoFull)) {
  throw "REPO_ROOT_MISSING: $repoFull"
}

Set-Location -LiteralPath $repoFull
$runner = Join-Path $repoFull 'devam.ps1'
if (-not (Test-Path -LiteralPath $runner)) {
  throw "CANONICAL_DEVAM_MISSING: $runner"
}

$statusDir = Join-Path $repoFull 'docs\chatgpt_status\_shared\status'
$heartbeatDir = Join-Path $repoFull 'docs\chatgpt_status\_shared\heartbeat'
if (-not (Test-Path -LiteralPath $statusDir)) { New-Item -ItemType Directory -Force -Path $statusDir | Out-Null }
if (-not (Test-Path -LiteralPath $heartbeatDir)) { New-Item -ItemType Directory -Force -Path $heartbeatDir | Out-Null }

$requestPath = Join-Path $statusDir 'local_reboot_runner_start_latest.json'
$now = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
@{
  requested_at = $now
  repo_root = $repoFull
  repo_full_name = $RepoFullName
  branch = $MainBranch
  max_tasks = $MaxTasks
  stale_minutes = $StaleMinutes
  new_parallel_runner_allowed = $false
  fake_completed_allowed = $false
  fake_final_ready_allowed = $false
  status = 'starting_canonical_devam'
} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $requestPath -Encoding UTF8

& powershell -NoProfile -ExecutionPolicy Bypass -File $runner -RepoRoot $repoFull -RepoFullName $RepoFullName -MainBranch $MainBranch -MaxTasks $MaxTasks -StaleMinutes $StaleMinutes
$code = $LASTEXITCODE

$donePath = Join-Path $statusDir 'local_reboot_runner_start_result_latest.json'
@{
  finished_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  exit_code = $code
  repo_root = $repoFull
  branch = $MainBranch
  runner = 'devam.ps1'
  status = if ($code -eq 0) { 'canonical_runner_invoked' } else { 'canonical_runner_failed' }
} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $donePath -Encoding UTF8

exit $code
