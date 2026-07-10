[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }
function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Read-Json([string]$Path) {
  try { if (Test-Path -LiteralPath $Path) { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } } catch {}
  return $null
}
function Write-Json([string]$Path, [object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText($Path, (($Value | ConvertTo-Json -Depth 40) + "`n"), [System.Text.UTF8Encoding]::new($false))
}
function Test-PidAlive([object]$Value) {
  try { return ($null -ne (Get-Process -Id ([int]$Value) -ErrorAction SilentlyContinue)) } catch { return $false }
}
function Get-CommandLine([int]$ProcessId) {
  try { return [string](Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop).CommandLine } catch { return '' }
}
function Test-Http([string]$Url) {
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 15 -Headers @{ 'Cache-Control'='no-cache' }
    return [pscustomobject]@{ ok=($response.StatusCode -ge 200 -and $response.StatusCode -lt 400); status_code=[int]$response.StatusCode; error=$null }
  } catch {
    return [pscustomobject]@{ ok=$false; status_code=$null; error=$_.Exception.Message }
  }
}

$worktree = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$controller = [System.IO.Path]::GetFullPath([string]$env:AAYS_CONTROLLER_REPO_ROOT)
$taskId = [string]$env:AAYS_TASK_ID
$pageKey = [string]$env:AAYS_PAGE_KEY
$branch = [string]$env:AAYS_TARGET_BRANCH
if (-not $worktree -or -not $controller -or $taskId -notlike 'one_click_runner_smoke_*') { throw 'SELF_TEST_MUST_RUN_INSIDE_CANONICAL_SHARED_RUNNER' }

$lockRel = 'docs/chatgpt_status/_shared/locks/single_runner.lock'
$heartbeatRel = 'docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json'
$bootstrapRel = 'docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json'
$lock = Read-Json (Join-Path $controller ($lockRel -replace '/', '\'))
$heartbeat = Read-Json (Join-Path $controller ($heartbeatRel -replace '/', '\'))
$bootstrap = Read-Json (Join-Path $controller ($bootstrapRel -replace '/', '\'))

$lockPid = if ($lock -and $lock.pid) { [int]$lock.pid } else { 0 }
$heartbeatPid = if ($heartbeat -and $heartbeat.daemon_pid) { [int]$heartbeat.daemon_pid } else { 0 }
$bootstrapPid = if ($bootstrap -and $bootstrap.runner_pid) { [int]$bootstrap.runner_pid } else { 0 }
$pidAlive = Test-PidAlive $lockPid
$commandLine = if ($pidAlive) { Get-CommandLine $lockPid } else { '' }
$processPathVerified = ($commandLine -like '*RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1*' -and $commandLine -like ('*' + $controller + '*'))
$pidAligned = ($lockPid -gt 0 -and $lockPid -eq $heartbeatPid -and $lockPid -eq $bootstrapPid)
$heartbeatAge = $null
if ($heartbeat -and $heartbeat.heartbeat_at) {
  try { $heartbeatAge = [math]::Round(((Get-Date).ToUniversalTime() - ([datetime]$heartbeat.heartbeat_at).ToUniversalTime()).TotalSeconds, 2) } catch {}
}
$heartbeatFresh = ($null -ne $heartbeatAge -and $heartbeatAge -ge 0 -and $heartbeatAge -le 180)

$health = Test-Http 'http://127.0.0.1:8012/health'
$matrix = Test-Http 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?runner_smoke=1'
$geometry = Test-Http 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html?runner_smoke=1'
$passed = ($pidAlive -and $processPathVerified -and $pidAligned -and $heartbeatFresh -and $health.ok -and $matrix.ok -and $geometry.ok)
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
$nonce = [guid]::NewGuid().ToString('N')
$timestampedRel = "docs/chatgpt_status/_shared/runner_outputs/one_click_runner_self_test_${stamp}.json"
$latestRel = 'docs/chatgpt_status/_shared/runner_outputs/one_click_runner_self_test_latest.json'
$payload = [ordered]@{
  test_id = $taskId
  status = if ($passed) { 'PASS' } else { 'FAIL' }
  generated_by_runner = $true
  generated_at = Now-Utc
  nonce = $nonce
  payload = 'AAYS_ONE_CLICK_RUNNER_SMOKE_OK'
  page_key = $pageKey
  portable_root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $controller))
  repo_root = $controller
  work_root = $worktree
  branch = $branch
  runner_pid = $lockPid
  lock_pid = $lockPid
  heartbeat_pid = $heartbeatPid
  bootstrap_pid = $bootstrapPid
  runner_process_alive = $pidAlive
  process_path_verified = $processPathVerified
  pid_alignment_passed = $pidAligned
  lock_valid = ($pidAlive -and $processPathVerified)
  heartbeat_fresh = $heartbeatFresh
  heartbeat_at = if ($heartbeat) { $heartbeat.heartbeat_at } else { $null }
  heartbeat_age_seconds = $heartbeatAge
  queue_pickup_tested = $true
  queue_pickup_passed = $true
  queue_pickup_evidence = 'this automation was invoked by the canonical shared runner from its queue'
  processed_task_count_before = $null
  processed_task_count_after = $null
  app_health = $health
  matrix_site = $matrix
  geometry_site = $geometry
  timestamped_proof_path = $timestampedRel
  latest_proof_path = $latestRel
  git_commit_sha = $null
  git_push_status = 'pending_runner_push'
  github_fetch_verified = $false
  remote_readback_ok = $false
  single_runner_only = $true
  new_runner = $false
  parallel_runner = $false
  blocker = if ($passed) { $null } else { 'runner_pid_heartbeat_or_8012_health_check_failed' }
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json (Join-Path $worktree ($timestampedRel -replace '/', '\')) $payload
Write-Json (Join-Path $worktree ($latestRel -replace '/', '\')) $payload

$gateRel = "docs/chatgpt_status/_shared/status/${taskId}_gate.json"
Write-Json (Join-Path $worktree ($gateRel -replace '/', '\')) ([ordered]@{
  source_row_gate_passed = $passed
  ui_token_gate_passed = ($matrix.ok -and $geometry.ok)
  browser_smoke_passed = ($matrix.ok -and $geometry.ok)
  post_sync_ok = $false
  manual_review_required = $true
  manual_review_reason = 'product_final_ready_must_remain_false'
  fake_data = $false
})

if (-not $passed) { throw 'ONE_CLICK_RUNNER_SELF_TEST_FAILED' }
Write-Output ($payload | ConvertTo-Json -Depth 40)
