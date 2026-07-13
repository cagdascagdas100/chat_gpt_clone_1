$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }

$taskId = 'aays1-137-next-batch-source-fetch-20260710'
$recoveryId = 'aays1-166-security-browser-cli-fallback-recovery-20260713'
$startedAt = (Get-Date).ToUniversalTime().ToString('o')

$script103Rel = 'docs/chatgpt_status/aays1/automation/103_security_accuracy_count_expansion.ps1'
$script145Rel = 'docs/chatgpt_status/aays1/automation/145_security_official_api_lsoa_validation.ps1'
$script147Rel = 'docs/chatgpt_status/aays1/automation/147_security_300_browser_validation.ps1'
$script146Rel = 'docs/chatgpt_status/aays1/automation/146_security_strict_multiwork_orchestrator.ps1'
$validatorRel = 'docs/chatgpt_status/aays1/automation/166_security_browser_validator.py'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/166_security_browser_cli_fallback_recovery.json'

$script103Path = Join-Path $repoRoot ($script103Rel -replace '/', '\')
$script145Path = Join-Path $repoRoot ($script145Rel -replace '/', '\')
$script147Path = Join-Path $repoRoot ($script147Rel -replace '/', '\')
$script146Path = Join-Path $repoRoot ($script146Rel -replace '/', '\')
$validatorPath = Join-Path $repoRoot ($validatorRel -replace '/', '\')
$outputPath = Join-Path $repoRoot ($outputRel -replace '/', '\')
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outputPath) | Out-Null

$result = [ordered]@{
  task_id = $taskId
  recovery_id = $recoveryId
  status = 'started'
  started_at = $startedAt
  completed_at = $null
  repo_root = $repoRoot
  canonical_storage = 'F_PORTABLE_ROOT'
  single_runner_only = $true
  parallel_runner = $false
  patched_scripts = @()
  parser_error_count_103 = $null
  parser_error_count_145 = $null
  parser_error_count_147 = $null
  validator_python_compile_exit_code = $null
  child_orchestrator = $script146Rel
  child_exit_code = $null
  child_output_tail = $null
  child_status = $null
  selected_verified_rows = $null
  added_rows = $null
  score_4_count = $null
  manual_review_count = $null
  official_latest_month = $null
  unique_lsoa_count = $null
  lsoa_http_200_count = $null
  browser_status = $null
  browser_engine = $null
  browser_url = $null
  latest_filter_rows = $null
  console_error_count = $null
  site_data_published = $false
  git_push_status = $null
  remote_readback_status = $null
  blockers = @()
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  person_level_data = $false
}

function Save-Result {
  $result | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $outputPath -Encoding UTF8
}

function Parse-ErrorCount([string]$path) {
  $tokens = $null
  $errors = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
  return @($errors).Count
}

function Read-Json([string]$rel) {
  $path = Join-Path $repoRoot ($rel -replace '/', '\')
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  try { return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}

try {
  foreach ($required in @($script103Path,$script145Path,$script146Path,$validatorPath)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "missing_required_file:$required" }
  }

  $source103 = Get-Content -LiteralPath $script103Path -Raw -Encoding UTF8
  $replacements103 = [ordered]@{
    'throw "baseline_count_not_$baselineExpected:$($baselineRows.Count)"' = 'throw "baseline_count_not_${baselineExpected}:$($baselineRows.Count)"'
    'features = @($verifiedFeatures)' = 'features = $verifiedFeatures.ToArray()'
    'rows = @($visibleRows)' = 'rows = $visibleRows.ToArray()'
    '$newRows = @($visibleRows | Where-Object { $_.is_new_in_latest_batch -eq $true })' = '$newRows = @($visibleRows.ToArray() | Where-Object { $_.is_new_in_latest_batch -eq $true })'
  }
  $changed103 = $false
  foreach ($pair in $replacements103.GetEnumerator()) {
    if ($source103.Contains($pair.Key)) {
      $source103 = $source103.Replace($pair.Key,$pair.Value)
      $changed103 = $true
    }
  }
  if ($changed103) {
    [System.IO.File]::WriteAllText($script103Path,$source103,[System.Text.UTF8Encoding]::new($false))
    $result.patched_scripts += $script103Rel
  }

  $source145 = Get-Content -LiteralPath $script145Path -Raw -Encoding UTF8
  $bad145 = '"lsoa_api_validation_failed:$lsoa:$($_.Exception.Message)"'
  $good145 = '"lsoa_api_validation_failed:${lsoa}:$($_.Exception.Message)"'
  if ($source145.Contains($bad145)) {
    $source145 = $source145.Replace($bad145,$good145)
    [System.IO.File]::WriteAllText($script145Path,$source145,[System.Text.UTF8Encoding]::new($false))
    $result.patched_scripts += $script145Rel
  }

  $wrapper147 = @'
$ErrorActionPreference = 'Continue'
$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$validator = Join-Path $repoRoot 'docs\chatgpt_status\aays1\automation\166_security_browser_validator.py'
$outPath = Join-Path $repoRoot 'docs\chatgpt_status\aays1\runner_outputs\147_security_300_browser_validation.json'
if (-not (Test-Path -LiteralPath $validator)) {
  $fallback = [ordered]@{
    task_id = 'aays1-147-security-300-browser-validation-20260711'
    page_key = 'aays1'
    status = 'blocked_300_rows_browser_exception'
    browser_status = 'not_run'
    blockers = @('missing_validator:docs/chatgpt_status/aays1/automation/166_security_browser_validator.py')
    single_runner_only = $true
    parallel_runner = $false
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  $fallback | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $outPath -Encoding UTF8
  exit 2
}
& python $validator $repoRoot
$code = $LASTEXITCODE
if (-not (Test-Path -LiteralPath $outPath)) {
  $fallback = [ordered]@{
    task_id = 'aays1-147-security-300-browser-validation-20260711'
    page_key = 'aays1'
    status = 'blocked_300_rows_browser_exception'
    browser_status = 'not_run'
    blockers = @('browser_validator_output_missing')
    single_runner_only = $true
    parallel_runner = $false
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  $fallback | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $outPath -Encoding UTF8
  exit 2
}
exit $code
'@
  [System.IO.File]::WriteAllText($script147Path,$wrapper147,[System.Text.UTF8Encoding]::new($false))
  $result.patched_scripts += $script147Rel

  $result.parser_error_count_103 = Parse-ErrorCount $script103Path
  $result.parser_error_count_145 = Parse-ErrorCount $script145Path
  $result.parser_error_count_147 = Parse-ErrorCount $script147Path
  if ($result.parser_error_count_103 -ne 0) { throw "103_parser_errors:$($result.parser_error_count_103)" }
  if ($result.parser_error_count_145 -ne 0) { throw "145_parser_errors:$($result.parser_error_count_145)" }
  if ($result.parser_error_count_147 -ne 0) { throw "147_parser_errors:$($result.parser_error_count_147)" }

  & python -m py_compile $validatorPath
  $result.validator_python_compile_exit_code = $LASTEXITCODE
  if ($result.validator_python_compile_exit_code -ne 0) { throw "validator_python_compile_exit_$($result.validator_python_compile_exit_code)" }

  Save-Result
  $childOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $script146Path 2>&1
  $result.child_exit_code = $LASTEXITCODE
  $childText = ($childOutput | Out-String).Trim()
  if ($childText.Length -gt 20000) { $childText = $childText.Substring($childText.Length - 20000) }
  $result.child_output_tail = $childText

  $out103 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json'
  $out145 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/145_security_official_api_lsoa_validation.json'
  $out147 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/147_security_300_browser_validation.json'
  $out146 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/146_security_strict_multiwork_orchestrator.json'

  if ($null -ne $out103) {
    $result.selected_verified_rows = $out103.selected_count
    $result.added_rows = $out103.added_count
    $result.score_4_count = $out103.score_4_count
    $result.manual_review_count = $out103.manual_review_count
  }
  if ($null -ne $out145) {
    $result.official_latest_month = $out145.official_latest_month
    $result.unique_lsoa_count = $out145.unique_lsoa_count
    $result.lsoa_http_200_count = $out145.lsoa_http_200_count
  }
  if ($null -ne $out147) {
    $result.browser_status = $out147.browser_status
    $result.browser_engine = $out147.browser_engine
    $result.browser_url = $out147.browser_url
    $result.latest_filter_rows = $out147.latest_filter_rows
    $result.console_error_count = $out147.console_error_count
  }
  if ($null -ne $out146) {
    $result.child_status = $out146.status
    $result.site_data_published = [bool]$out146.site_data_published
    $result.git_push_status = $out146.git_push_status
    $result.remote_readback_status = $out146.remote_readback_status
    if ($out146.blockers) { $result.blockers += @($out146.blockers | ForEach-Object { "146:$_" }) }
  }

  if ($result.child_exit_code -eq 0 -and $result.child_status -eq 'completed_atomic_publish_remote_readback_pass') {
    $result.status = 'browser_cli_fallback_strict_chain_completed'
  } else {
    $result.status = 'browser_cli_fallback_strict_chain_blocked'
    if ($result.child_exit_code -ne 0) { $result.blockers += "child_orchestrator_exit_$($result.child_exit_code)" }
  }
} catch {
  $result.status = 'blocked_browser_cli_fallback_recovery'
  $result.blockers += $_.Exception.Message
} finally {
  $result.completed_at = (Get-Date).ToUniversalTime().ToString('o')
  $result.blockers = @($result.blockers | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | Select-Object -Unique)
  Save-Result
}

Write-Host "OUTPUT=$outputPath"
if ($result.blockers.Count -gt 0 -or $result.child_exit_code -notin @(0,$null)) { exit 2 }
exit 0
