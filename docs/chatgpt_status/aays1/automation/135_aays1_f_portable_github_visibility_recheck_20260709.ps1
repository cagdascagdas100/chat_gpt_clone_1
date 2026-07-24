# AAYS aays1 F portable GitHub visibility recheck.
# Runs inside the existing single shared runner only. No new runner, no parallel runner.
# Reads runner proof files and writes an aays1 report/status proving whether ChatGPT can verify outputs from GitHub.

$ErrorActionPreference = 'Stop'

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
Set-Location -LiteralPath $repoRoot

function Read-JsonProof([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    return [pscustomobject]@{ exists = $false; path = $Path; parse_ok = $false; data = $null; error = 'missing' }
  }
  try {
    $data = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    return [pscustomobject]@{ exists = $true; path = $Path; parse_ok = $true; data = $data; error = '' }
  } catch {
    return [pscustomobject]@{ exists = $true; path = $Path; parse_ok = $false; data = $null; error = $_.Exception.Message }
  }
}

$proofPaths = [ordered]@{
  recovery_test = 'docs/chatgpt_status/aays1/status/134_f_portable_one_click_recovery_test_latest.json'
  bootstrap_latest = 'docs/chatgpt_status/aays1/status/130_f_portable_one_click_recovery_bootstrap_latest.json'
  heartbeat_latest = 'docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json'
  runner_bootstrap = 'docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json'
  single_runner_lock = 'docs/chatgpt_status/_shared/locks/single_runner.lock'
}

$proofs = [ordered]@{}
foreach ($k in $proofPaths.Keys) { $proofs[$k] = Read-JsonProof $proofPaths[$k] }

$main = $proofs.recovery_test.data
$lock = $proofs.single_runner_lock.data

$healthy = $false
$blockers = New-Object System.Collections.Generic.List[string]
foreach ($k in $proofs.Keys) {
  if (-not $proofs[$k].exists) { [void]$blockers.Add("MISSING_$k") }
  elseif (-not $proofs[$k].parse_ok) { [void]$blockers.Add("PARSE_FAILED_$k") }
}

if ($main) {
  if ($main.runner_active -ne $true) { [void]$blockers.Add('RUNNER_ACTIVE_NOT_TRUE') }
  if ($main.pid_alive -ne $true) { [void]$blockers.Add('PID_ALIVE_NOT_TRUE') }
  if ($main.lock_valid -ne $true) { [void]$blockers.Add('LOCK_VALID_NOT_TRUE') }
  if ([string]$main.git_push_status -ne 'pushed') { [void]$blockers.Add('GIT_PUSH_STATUS_NOT_PUSHED') }
  if ($main.final_ready -ne $false) { [void]$blockers.Add('FINAL_READY_NOT_FALSE') }
  if ($main.fake_data -ne $false) { [void]$blockers.Add('FAKE_DATA_NOT_FALSE') }
  if ($main.db_write -ne $false) { [void]$blockers.Add('DB_WRITE_NOT_FALSE') }
  if ($main.migration -ne $false) { [void]$blockers.Add('MIGRATION_NOT_FALSE') }
  if ($main.production_deploy -ne $false) { [void]$blockers.Add('PRODUCTION_DEPLOY_NOT_FALSE') }
} else {
  [void]$blockers.Add('MAIN_PROOF_MISSING')
}

if ($lock -and $main) {
  if ([int]$lock.pid -ne [int]$main.pid) { [void]$blockers.Add('LOCK_PID_MISMATCH') }
}

$healthy = ($blockers.Count -eq 0)

$statusDir = 'docs/chatgpt_status/aays1/status'
$reportDir = 'docs/chatgpt_status/aays1/reports'
New-Item -ItemType Directory -Force -Path $statusDir,$reportDir | Out-Null

$statusPath = Join-Path $statusDir '135_aays1_f_portable_github_visibility_recheck_latest.json'
$reportPath = Join-Path $reportDir 'f_portable_one_click_runner_github_report_test_20260709.md'

$status = [ordered]@{
  task_id = '135_aays1_f_portable_github_visibility_recheck_20260709'
  page_key = 'aays1'
  checked_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  runner_active = if ($main) { [bool]$main.runner_active } else { $false }
  pid = if ($main) { $main.pid } else { $null }
  pid_alive = if ($main) { [bool]$main.pid_alive } else { $false }
  lock_valid = if ($main) { [bool]$main.lock_valid } else { $false }
  git_push_status = if ($main) { [string]$main.git_push_status } else { 'missing' }
  output_pushed_to_github = if ($main) { [bool]$main.output_pushed_to_github } else { $false }
  ChatGPT_can_verify_from_GitHub = $healthy
  proof_files_checked = $proofPaths.Values
  missing_or_failed_proofs = @($blockers)
  single_runner_only = $true
  new_runner = $false
  parallel_runner = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$status | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $statusPath -Encoding UTF8

$lines = @()
$lines += '# F Portable One Click Runner GitHub Report Test'
$lines += ''
$lines += "- checked_at_utc: $($status.checked_at_utc)"
$lines += "- portable_root: $(if ($main) { $main.portable_root } else { 'missing' })"
$lines += "- repo_root: $(if ($main) { $main.repo_root } else { 'missing' })"
$lines += "- launcher_path: $(if ($main) { $main.launcher_path } else { 'missing' })"
$lines += "- runner_active: $($status.runner_active)"
$lines += "- pid: $($status.pid)"
$lines += "- pid_alive: $($status.pid_alive)"
$lines += "- lock_valid: $($status.lock_valid)"
$lines += "- git_push_status: $($status.git_push_status)"
$lines += "- output_pushed_to_github: $($status.output_pushed_to_github)"
$lines += "- ChatGPT_can_verify_from_GitHub: $($status.ChatGPT_can_verify_from_GitHub)"
$lines += "- single_runner_only: true"
$lines += "- new_runner: false"
$lines += "- parallel_runner: false"
$lines += "- final_ready: false"
$lines += "- fake_data: false"
$lines += "- db_write: false"
$lines += "- migration: false"
$lines += "- production_deploy: false"
$lines += ''
$lines += '## Proof files checked'
foreach ($p in $proofPaths.Values) { $lines += "- $p" }
$lines += ''
$lines += '## Remaining blockers'
if ($blockers.Count -eq 0) { $lines += '- none' } else { foreach ($b in $blockers) { $lines += "- $b" } }
$lines += ''
$lines += 'This report is generated by the existing F portable single shared runner task only; it does not mark product final readiness.'
$lines -join "`r`n" | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Output 'AAYS1_F_PORTABLE_GITHUB_VISIBILITY_RECHECK=true'
Write-Output "runner_active=$($status.runner_active)"
Write-Output "pid_alive=$($status.pid_alive)"
Write-Output "lock_valid=$($status.lock_valid)"
Write-Output "git_push_status=$($status.git_push_status)"
Write-Output "ChatGPT_can_verify_from_GitHub=$($status.ChatGPT_can_verify_from_GitHub)"
Write-Output "remaining_blockers=$($blockers.Count)"
Write-Output 'final_ready=false'
