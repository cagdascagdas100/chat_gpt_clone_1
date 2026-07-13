$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }

$taskId = 'aays1-137-next-batch-source-fetch-20260710'
$recoveryId = 'aays1-163-security-103-generic-list-recovery-20260713'
$branch = 'codex/aays-single-runner-v5-20260706'
$startedAt = (Get-Date).ToUniversalTime().ToString('o')

$script103Rel = 'docs/chatgpt_status/aays1/automation/103_security_accuracy_count_expansion.ps1'
$script146Rel = 'docs/chatgpt_status/aays1/automation/146_security_strict_multiwork_orchestrator.ps1'
$output103Rel = 'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json'
$output146Rel = 'docs/chatgpt_status/aays1/runner_outputs/146_security_strict_multiwork_orchestrator.json'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/163_security_103_generic_list_recovery_orchestrator.json'

$script103Path = Join-Path $repoRoot ($script103Rel -replace '/', '\')
$script146Path = Join-Path $repoRoot ($script146Rel -replace '/', '\')
$output103Path = Join-Path $repoRoot ($output103Rel -replace '/', '\')
$output146Path = Join-Path $repoRoot ($output146Rel -replace '/', '\')
$outputPath = Join-Path $repoRoot ($outputRel -replace '/', '\')
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outputPath) | Out-Null

$sitePaths = @(
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv',
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson',
  'england_map_web/data/security_public_safety/security_evidence_manifest.json',
  'england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json',
  'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json',
  'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json'
)

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
  repaired_script = $script103Rel
  parser_error_count = $null
  runtime_fix_count = 0
  runtime_fixes = @()
  expansion_exit_code = $null
  expansion_output_tail = $null
  expansion_output_exists = $false
  expansion_status = $null
  source_feature_count = $null
  baseline_rows_preserved = $null
  selected_count = $null
  added_count = $null
  score_4_count = $null
  manual_review_count = $null
  csv_geojson_count_parity = $null
  strict_orchestrator_exit_code = $null
  strict_orchestrator_output_tail = $null
  strict_orchestrator_status = $null
  site_data_restored_after_blocker = $false
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

function Read-JsonSafe([string]$path) {
  try {
    if (Test-Path -LiteralPath $path) { return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json }
  } catch {}
  return $null
}

function Invoke-Captured([string]$scriptPath) {
  $lines = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath 2>&1
  $code = $LASTEXITCODE
  $text = ($lines | Out-String).Trim()
  if ($text.Length -gt 16000) { $text = $text.Substring($text.Length - 16000) }
  return [pscustomobject]@{ ExitCode=$code; Text=$text }
}

function Restore-SiteBaseline {
  try {
    Push-Location $repoRoot
    $fetch = Start-Process -FilePath 'git.exe' -ArgumentList @('fetch','origin',$branch) -NoNewWindow -Wait -PassThru
    if ($fetch.ExitCode -ne 0) { throw "git_fetch_exit_$($fetch.ExitCode)" }
    $restoreArgs = @('restore','--source',"origin/$branch",'--') + $sitePaths
    $restore = Start-Process -FilePath 'git.exe' -ArgumentList $restoreArgs -NoNewWindow -Wait -PassThru
    if ($restore.ExitCode -ne 0) { throw "git_restore_exit_$($restore.ExitCode)" }
    $result.site_data_restored_after_blocker = $true
  } catch {
    $result.blockers += "site_data_restore_failed:$($_.Exception.Message)"
  } finally {
    try { Pop-Location } catch {}
  }
}

try {
  if (-not (Test-Path -LiteralPath $script103Path)) { throw "missing_script:$script103Rel" }
  if (-not (Test-Path -LiteralPath $script146Path)) { throw "missing_script:$script146Rel" }

  $source = Get-Content -LiteralPath $script103Path -Raw -Encoding UTF8
  $replacements = @(
    [pscustomobject]@{ Name='verified_features_to_array'; Bad='features = @($verifiedFeatures)'; Good='features = $verifiedFeatures.ToArray()' },
    [pscustomobject]@{ Name='visible_rows_to_array'; Bad='rows = @($visibleRows)'; Good='rows = $visibleRows.ToArray()' },
    [pscustomobject]@{ Name='new_rows_to_array'; Bad='$newRows = @($visibleRows | Where-Object { $_.is_new_in_latest_batch -eq $true })'; Good='$newRows = @($visibleRows.ToArray() | Where-Object { $_.is_new_in_latest_batch -eq $true })' }
  )

  foreach ($replacement in $replacements) {
    if ($source.Contains($replacement.Bad)) {
      $source = $source.Replace($replacement.Bad, $replacement.Good)
      $result.runtime_fix_count++
      $result.runtime_fixes += $replacement.Name
    } elseif (-not $source.Contains($replacement.Good)) {
      throw "expected_runtime_signature_missing:$($replacement.Name)"
    }
  }

  [System.IO.File]::WriteAllText($script103Path, $source, [System.Text.UTF8Encoding]::new($false))

  $tokens = $null
  $parseErrors = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($script103Path, [ref]$tokens, [ref]$parseErrors)
  $result.parser_error_count = @($parseErrors).Count
  if ($result.parser_error_count -ne 0) {
    $messages = @($parseErrors | ForEach-Object { [string]$_.Message })
    throw ('103_parser_validation_failed:' + ($messages -join ' | '))
  }

  Save-Result
  $run103 = Invoke-Captured $script103Path
  $result.expansion_exit_code = $run103.ExitCode
  $result.expansion_output_tail = $run103.Text
  $result.expansion_output_exists = Test-Path -LiteralPath $output103Path

  $out103 = Read-JsonSafe $output103Path
  if ($null -ne $out103) {
    $result.expansion_status = [string]$out103.status
    $result.source_feature_count = $out103.source_feature_count
    $result.baseline_rows_preserved = $out103.baseline_rows_preserved
    $result.selected_count = $out103.selected_count
    $result.added_count = $out103.added_count
    $result.score_4_count = $out103.score_4_count
    $result.manual_review_count = $out103.manual_review_count
    $result.csv_geojson_count_parity = $out103.csv_geojson_count_parity
    if ($out103.blockers) { $result.blockers += @($out103.blockers | ForEach-Object { "103:$_" }) }
  } else {
    $result.blockers += '103_output_missing_or_invalid'
  }

  $expansionPass = (
    $run103.ExitCode -eq 0 -and
    $null -ne $out103 -and
    $out103.selected_count -eq 300 -and
    $out103.added_count -eq 150 -and
    $out103.score_4_count -eq 300 -and
    $out103.manual_review_count -eq 0 -and
    $out103.csv_geojson_count_parity -eq $true
  )

  if (-not $expansionPass) {
    $result.blockers += '103_strict_expansion_gate_not_passed'
    Restore-SiteBaseline
    $result.status = 'blocked_after_generic_list_recovery'
  } else {
    Save-Result
    $run146 = Invoke-Captured $script146Path
    $result.strict_orchestrator_exit_code = $run146.ExitCode
    $result.strict_orchestrator_output_tail = $run146.Text
    $out146 = Read-JsonSafe $output146Path
    if ($null -ne $out146) {
      $result.strict_orchestrator_status = [string]$out146.status
      if ($out146.blockers) { $result.blockers += @($out146.blockers | ForEach-Object { "146:$_" }) }
    } else {
      $result.blockers += '146_output_missing_or_invalid'
    }
    if ($run146.ExitCode -eq 0 -and $null -ne $out146 -and $out146.site_data_published -eq $true -and $out146.remote_readback_status -eq 'passed') {
      $result.status = 'generic_list_fixed_strict_chain_completed'
    } else {
      $result.status = 'generic_list_fixed_strict_chain_blocked'
      if (-not $result.blockers) { $result.blockers += "146_exit_$($run146.ExitCode)" }
    }
  }
}
catch {
  $result.status = 'blocked_generic_list_recovery_exception'
  $result.blockers += $_.Exception.Message
  Restore-SiteBaseline
}
finally {
  $result.completed_at = (Get-Date).ToUniversalTime().ToString('o')
  Save-Result
}

Write-Host "OUTPUT=$outputPath"
if ($result.blockers.Count -gt 0 -or $result.status -notin @('generic_list_fixed_strict_chain_completed')) { exit 2 }
exit 0
