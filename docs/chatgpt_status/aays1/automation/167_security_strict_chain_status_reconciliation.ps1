$ErrorActionPreference = 'Continue'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }

$taskId = 'aays1-137-next-batch-source-fetch-20260710'
$recoveryId = 'aays1-167-security-strict-chain-status-reconciliation-20260713'
$script166Rel = 'docs/chatgpt_status/aays1/automation/166_security_browser_cli_fallback_recovery.ps1'
$out167Rel = 'docs/chatgpt_status/aays1/runner_outputs/167_security_strict_chain_status_reconciliation.json'
$out167Path = Join-Path $repoRoot ($out167Rel -replace '/', '\')
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $out167Path) | Out-Null

function Read-Json([string]$rel) {
  $path = Join-Path $repoRoot ($rel -replace '/', '\')
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  try { return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}

function Bool-Value($value) {
  if ($value -is [bool]) { return [bool]$value }
  return ([string]$value).Trim().ToLowerInvariant() -eq 'true'
}

$result = [ordered]@{
  task_id = $taskId
  recovery_id = $recoveryId
  page_key = 'aays1'
  status = 'started'
  started_at = (Get-Date).ToUniversalTime().ToString('o')
  completed_at = $null
  repo_root = $repoRoot
  canonical_storage = 'F_PORTABLE_ROOT'
  single_runner_only = $true
  parallel_runner = $false
  execution_mode = 'single_runner_sequential_multiwork'
  requested_subtask_count = 15
  child_166_exit_code = $null
  child_166_status = $null
  child_146_status = $null
  candidate_source_features = $null
  selected_verified_rows = $null
  added_rows = $null
  score_4_count = $null
  manual_review_count = $null
  csv_geojson_count_parity = $false
  official_latest_month = $null
  unique_lsoa_count = $null
  lsoa_http_200_count = $null
  lsoa_failed_count = $null
  browser_status = $null
  browser_engine = $null
  latest_filter_rows = $null
  console_error_count = $null
  site_data_published = $false
  git_push_status = $null
  remote_readback_status = $null
  strict_103_pass = $false
  strict_145_pass = $false
  strict_147_pass = $false
  strict_146_publish_pass = $false
  completed_gate_count = 0
  total_gate_count = 4
  blockers = @()
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  person_level_data = $false
}

try {
  $script166Path = Join-Path $repoRoot ($script166Rel -replace '/', '\')
  if (-not (Test-Path -LiteralPath $script166Path)) { throw "missing_166_script:$script166Rel" }

  $childText = & powershell -NoProfile -ExecutionPolicy Bypass -File $script166Path 2>&1
  $result.child_166_exit_code = $LASTEXITCODE

  $out166 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/166_security_browser_cli_fallback_recovery.json'
  $out103 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json'
  $out145 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/145_security_official_api_lsoa_validation.json'
  $out147 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/147_security_300_browser_validation.json'
  $out146 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/146_security_strict_multiwork_orchestrator.json'

  if ($null -ne $out166) { $result.child_166_status = [string]$out166.status }

  if ($null -ne $out103) {
    $result.candidate_source_features = $out103.source_feature_count
    $result.selected_verified_rows = $out103.selected_count
    $result.added_rows = $out103.added_count
    $result.score_4_count = $out103.score_4_count
    $result.manual_review_count = $out103.manual_review_count
    $result.csv_geojson_count_parity = Bool-Value $out103.csv_geojson_count_parity
    $result.strict_103_pass = (
      [int]$out103.selected_count -eq 300 -and
      [int]$out103.added_count -eq 150 -and
      [int]$out103.score_4_count -eq 300 -and
      [int]$out103.manual_review_count -eq 0 -and
      (Bool-Value $out103.csv_geojson_count_parity)
    )
  }

  if ($null -ne $out145) {
    $result.official_latest_month = $out145.official_latest_month
    $result.unique_lsoa_count = $out145.unique_lsoa_count
    $result.lsoa_http_200_count = $out145.lsoa_http_200_count
    $result.lsoa_failed_count = $out145.lsoa_failed_count
    $result.strict_145_pass = (
      [string]$out145.status -eq 'completed_all_lsoa_official_api_validated' -and
      [int]$out145.lsoa_failed_count -eq 0 -and
      [int]$out145.lsoa_http_200_count -gt 0 -and
      [int]$out145.lsoa_http_200_count -eq [int]$out145.unique_lsoa_count
    )
  }

  if ($null -ne $out147) {
    $result.browser_status = $out147.browser_status
    $result.browser_engine = $out147.browser_engine
    $result.latest_filter_rows = $out147.latest_filter_rows
    $result.console_error_count = $out147.console_error_count
    $result.strict_147_pass = (
      [string]$out147.browser_status -eq 'pass' -and
      [int]$out147.console_error_count -eq 0 -and
      [string]$out147.latest_filter_rows -match '150 satır'
    )
  }

  if ($null -ne $out146) {
    $result.child_146_status = [string]$out146.status
    $result.site_data_published = Bool-Value $out146.site_data_published
    $result.git_push_status = $out146.git_push_status
    $result.remote_readback_status = $out146.remote_readback_status
    $result.strict_146_publish_pass = (
      (Bool-Value $out146.site_data_published) -and
      [string]$out146.remote_readback_status -eq 'passed' -and
      [string]$out146.git_push_status -in @('pushed','no_changes_to_push') -and
      [string]$out146.status -in @(
        'completed_300_verified_internet_validated_browser_pass_final_false',
        'completed_atomic_publish_remote_readback_pass'
      )
    )
    if ($out146.blockers) { $result.blockers += @($out146.blockers | ForEach-Object { "146:$_" }) }
  }

  $result.completed_gate_count = @(
    $result.strict_103_pass,
    $result.strict_145_pass,
    $result.strict_147_pass,
    $result.strict_146_publish_pass
  ).Where({ $_ -eq $true }).Count

  if (-not $result.strict_103_pass) { $result.blockers += 'strict_103_gate_not_passed' }
  if (-not $result.strict_145_pass) { $result.blockers += 'strict_145_gate_not_passed' }
  if (-not $result.strict_147_pass) { $result.blockers += 'strict_147_gate_not_passed' }
  if (-not $result.strict_146_publish_pass) { $result.blockers += 'strict_146_publish_remote_readback_gate_not_passed' }

  if ($result.completed_gate_count -eq $result.total_gate_count) {
    $result.status = 'completed_strict_chain_remote_readback_pass_final_false'
    $result.blockers = @()
  } else {
    $result.status = 'blocked_strict_chain_status_reconciliation'
    if ($result.child_166_exit_code -ne 0) { $result.blockers += "child_166_exit_$($result.child_166_exit_code)" }
  }
} catch {
  $result.status = 'blocked_strict_chain_status_reconciliation'
  $result.blockers += $_.Exception.Message
} finally {
  $result.completed_at = (Get-Date).ToUniversalTime().ToString('o')
  $result.blockers = @($result.blockers | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | Select-Object -Unique)
  $result.final_ready = $false
  $result.product_final_ready = $false
  $result | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $out167Path -Encoding UTF8
}

Write-Host "OUTPUT=$out167Path"
if ($result.completed_gate_count -ne $result.total_gate_count -or $result.blockers.Count -gt 0) { exit 2 }
exit 0
