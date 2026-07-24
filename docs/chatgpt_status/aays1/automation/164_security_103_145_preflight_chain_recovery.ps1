$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }

$taskId = 'aays1-137-next-batch-source-fetch-20260710'
$recoveryId = 'aays1-164-security-103-145-preflight-chain-recovery-20260713'
$startedAt = (Get-Date).ToUniversalTime().ToString('o')

$script103Rel = 'docs/chatgpt_status/aays1/automation/103_security_accuracy_count_expansion.ps1'
$script145Rel = 'docs/chatgpt_status/aays1/automation/145_security_official_api_lsoa_validation.ps1'
$script146Rel = 'docs/chatgpt_status/aays1/automation/146_security_strict_multiwork_orchestrator.ps1'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/164_security_103_145_preflight_chain_recovery.json'

$script103Path = Join-Path $repoRoot ($script103Rel -replace '/', '\')
$script145Path = Join-Path $repoRoot ($script145Rel -replace '/', '\')
$script146Path = Join-Path $repoRoot ($script146Rel -replace '/', '\')
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
  patch_count = 0
  parser_error_count_103 = $null
  parser_error_count_145 = $null
  parser_errors_103 = @()
  parser_errors_145 = @()
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

function Patch-TextFile([string]$path, [hashtable]$replacements, [string]$label) {
  if (-not (Test-Path -LiteralPath $path)) { throw "missing_script:$label" }
  $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
  $changed = $false
  foreach ($key in $replacements.Keys) {
    $value = [string]$replacements[$key]
    if ($text.Contains([string]$key)) {
      $text = $text.Replace([string]$key, $value)
      $result.patch_count++
      $changed = $true
    }
  }
  if ($changed) {
    [System.IO.File]::WriteAllText($path, $text, [System.Text.UTF8Encoding]::new($false))
    $result.patched_scripts += $label
  }
}

function Get-ParserErrors([string]$path) {
  $tokens = $null
  $errors = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
  return @($errors)
}

function Read-Json([string]$rel) {
  $path = Join-Path $repoRoot ($rel -replace '/', '\')
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  try { return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}

try {
  if (-not (Test-Path -LiteralPath $script146Path)) { throw "missing_script:$script146Rel" }

  $replace103 = @{
    'throw "baseline_count_not_$baselineExpected:$($baselineRows.Count)"' = 'throw "baseline_count_not_${baselineExpected}:$($baselineRows.Count)"'
    'features = @($verifiedFeatures)' = 'features = $verifiedFeatures.ToArray()'
    'rows = @($visibleRows)' = 'rows = $visibleRows.ToArray()'
    '$newRows = @($visibleRows | Where-Object { $_.is_new_in_latest_batch -eq $true })' = '$newRows = @($visibleRows.ToArray() | Where-Object { $_.is_new_in_latest_batch -eq $true })'
  }
  Patch-TextFile -path $script103Path -replacements $replace103 -label $script103Rel

  $replace145 = @{
    '"lsoa_api_validation_failed:$lsoa:$($_.Exception.Message)"' = '"lsoa_api_validation_failed:${lsoa}:$($_.Exception.Message)"'
  }
  Patch-TextFile -path $script145Path -replacements $replace145 -label $script145Rel

  $errors103 = @(Get-ParserErrors $script103Path)
  $errors145 = @(Get-ParserErrors $script145Path)
  $result.parser_error_count_103 = $errors103.Count
  $result.parser_error_count_145 = $errors145.Count
  $result.parser_errors_103 = @($errors103 | ForEach-Object { [string]$_.Message })
  $result.parser_errors_145 = @($errors145 | ForEach-Object { [string]$_.Message })
  if ($errors103.Count -ne 0) { throw ('103_parser_validation_failed:' + ($result.parser_errors_103 -join ' | ')) }
  if ($errors145.Count -ne 0) { throw ('145_parser_validation_failed:' + ($result.parser_errors_145 -join ' | ')) }

  Save-Result
  $childOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $script146Path 2>&1
  $childCode = $LASTEXITCODE
  $result.child_exit_code = $childCode
  $childText = ($childOutput | Out-String).Trim()
  if ($childText.Length -gt 16000) { $childText = $childText.Substring($childText.Length - 16000) }
  $result.child_output_tail = $childText

  $out146 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/146_security_strict_multiwork_orchestrator.json'
  $out103 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json'
  $out145 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/145_security_official_api_lsoa_validation.json'
  $out147 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/147_security_300_browser_validation.json'

  if ($null -ne $out146) {
    $result.child_status = [string]$out146.status
    $result.site_data_published = [bool]$out146.site_data_published
    $result.git_push_status = [string]$out146.git_push_status
    $result.remote_readback_status = [string]$out146.remote_readback_status
    if ($out146.blockers) { $result.blockers += @($out146.blockers | ForEach-Object { "146:$_" }) }
  } else {
    $result.blockers += 'missing_or_invalid_output:146_security_strict_multiwork_orchestrator.json'
  }
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
    $result.latest_filter_rows = $out147.latest_filter_rows
    $result.console_error_count = $out147.console_error_count
  }

  if ($childCode -eq 0 -and $null -ne $out146 -and $out146.status -eq 'published_300_verified_internet_validated_browser_pass' -and $out146.site_data_published -eq $true -and $out146.remote_readback_status -eq 'passed') {
    $result.status = 'preflight_fixed_strict_chain_published'
  } else {
    $result.status = 'preflight_fixed_strict_chain_blocked'
    if ($childCode -ne 0) { $result.blockers += "child_orchestrator_exit_$childCode" }
  }
}
catch {
  $result.status = 'blocked_preflight_recovery'
  $result.blockers += $_.Exception.Message
}
finally {
  $result.completed_at = (Get-Date).ToUniversalTime().ToString('o')
  Save-Result
}

Write-Host "OUTPUT=$outputPath"
if ($result.blockers.Count -gt 0 -or $result.child_exit_code -notin @(0,$null)) { exit 2 }
exit 0
