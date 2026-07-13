$ErrorActionPreference = 'Continue'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$branch = 'codex/aays-single-runner-v5-20260706'
$outRel = 'docs/chatgpt_status/aays1/runner_outputs/146_security_strict_multiwork_orchestrator.json'
$outPath = Join-Path $repoRoot $outRel
New-Item -ItemType Directory -Force -Path (Split-Path $outPath) | Out-Null

$sitePaths = @(
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv',
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson',
  'england_map_web/data/security_public_safety/security_evidence_manifest.json',
  'england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json',
  'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json',
  'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json'
)

$evidencePaths = @(
  'docs/chatgpt_status/aays1/runner_outputs/142_security_site_row_evidence_visibility_fix.json',
  'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json',
  'docs/chatgpt_status/aays1/runner_outputs/145_security_official_api_lsoa_validation.json',
  'docs/chatgpt_status/aays1/runner_outputs/147_security_300_browser_validation.json',
  $outRel,
  'docs/chatgpt_status/aays1/reports/142_security_site_row_evidence_visibility_fix_completion_20260711.md',
  'docs/chatgpt_status/aays1/reports/137_security_verified_expansion_latest.md',
  'docs/chatgpt_status/aays1/reports/145_security_official_api_lsoa_validation_latest.md',
  'docs/chatgpt_status/_shared/reports/security_row_evidence_browser_validation_20260711.json',
  'docs/chatgpt_status/_shared/reports/security_300_rows_browser_validation_20260711.json'
)

function Read-Json([string]$rel) {
  $path = Join-Path $repoRoot $rel
  if (-not (Test-Path $path)) { return $null }
  try { return Get-Content -Raw -Encoding UTF8 $path | ConvertFrom-Json } catch { return $null }
}

function Invoke-Child([string]$scriptRel, [string]$outputRel) {
  $scriptPath = Join-Path $repoRoot $scriptRel
  $item = [ordered]@{ script=$scriptRel; exists=(Test-Path $scriptPath); exit_code=$null; status='not_run'; output_path=$outputRel; output_status=$null; blockers=@() }
  if (-not $item.exists) {
    $item.status = 'missing_script'
    $item.blockers += "missing_script:$scriptRel"
    return [pscustomobject]$item
  }
  try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath
    $item.exit_code = $LASTEXITCODE
    $item.status = if ($LASTEXITCODE -eq 0) { 'completed' } else { 'completed_with_nonzero_exit' }
  } catch {
    $item.status = 'exception'
    $item.blockers += $_.Exception.Message
  }
  $child = Read-Json $outputRel
  if ($null -eq $child) {
    $item.blockers += "missing_or_invalid_output:$outputRel"
  } else {
    $item.output_status = [string]$child.status
    if ($child.blockers) { $item.blockers += @($child.blockers) }
  }
  return [pscustomobject]$item
}

$result = [ordered]@{
  task_id = 'aays1-137-next-batch-source-fetch-20260710'
  orchestrator_id = 'aays1-146-security-strict-multiwork-orchestrator-20260711'
  page_key = 'aays1'
  implementation = 'visibility_then_300_then_all_lsoa_api_then_browser_atomic_publish_v1'
  status = 'started'
  checked_at = (Get-Date).ToString('o')
  branch = $branch
  repo_root = $repoRoot
  canonical_storage = 'F_PORTABLE_ROOT'
  single_runner_only = $true
  parallel_runner = $false
  requested_subtask_count = 15
  child_steps = @()
  baseline_visible_rows = $null
  candidate_source_features = $null
  selected_verified_rows = $null
  added_rows = $null
  accuracy_score_4_count = $null
  manual_review_count = $null
  unique_lsoa_count = $null
  lsoa_http_200_count = $null
  official_latest_month = $null
  browser_300_status = $null
  browser_latest_filter_rows = $null
  console_error_count = $null
  site_data_publish_allowed = $false
  site_data_published = $false
  site_data_restored_after_blocker = $false
  git_push_status = 'not_attempted'
  remote_readback_status = 'not_attempted'
  commit_sha = $null
  blockers = @()
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  person_level_data = $false
}

$baselineStatus = Read-Json 'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json'
if ($null -ne $baselineStatus) { $result.baseline_visible_rows = $baselineStatus.verified_csv_rows }

$visibilityOutput = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/142_security_site_row_evidence_visibility_fix.json'
if ($null -eq $visibilityOutput -or $visibilityOutput.browser_smoke_status -ne 'pass') {
  $step142 = Invoke-Child 'docs/chatgpt_status/aays1/automation/142_security_site_row_evidence_visibility_fix.ps1' 'docs/chatgpt_status/aays1/runner_outputs/142_security_site_row_evidence_visibility_fix.json'
  $result.child_steps += $step142
  if ($step142.blockers) { $result.blockers += @($step142.blockers | ForEach-Object { "142:$_" }) }
  $visibilityOutput = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/142_security_site_row_evidence_visibility_fix.json'
} else {
  $result.child_steps += [pscustomobject]@{ script='docs/chatgpt_status/aays1/automation/142_security_site_row_evidence_visibility_fix.ps1'; exists=$true; exit_code=0; status='already_passed'; output_path='docs/chatgpt_status/aays1/runner_outputs/142_security_site_row_evidence_visibility_fix.json'; output_status=$visibilityOutput.status; blockers=@() }
}

$visibilityPass = ($null -ne $visibilityOutput -and $visibilityOutput.browser_smoke_status -eq 'pass' -and $visibilityOutput.console_error_count -eq 0)
if (-not $visibilityPass) { $result.blockers += 'visibility_browser_gate_not_passed_before_expansion' }

if ($visibilityPass) {
  $step103 = Invoke-Child 'docs/chatgpt_status/aays1/automation/103_security_accuracy_count_expansion.ps1' 'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json'
  $result.child_steps += $step103
  if ($step103.blockers) { $result.blockers += @($step103.blockers | ForEach-Object { "103:$_" }) }
  $out103 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json'
  if ($null -ne $out103) {
    $result.candidate_source_features = $out103.source_feature_count
    $result.selected_verified_rows = $out103.selected_count
    $result.added_rows = $out103.added_count
    $result.accuracy_score_4_count = $out103.score_4_count
    $result.manual_review_count = $out103.manual_review_count
  }

  $expansionPass = ($step103.exit_code -eq 0 -and $null -ne $out103 -and $out103.selected_count -eq 300 -and $out103.score_4_count -eq 300 -and $out103.manual_review_count -eq 0 -and $out103.csv_geojson_count_parity -eq $true)
  if (-not $expansionPass) { $result.blockers += 'strict_300_expansion_gate_not_passed' }

  if ($expansionPass) {
    $step145 = Invoke-Child 'docs/chatgpt_status/aays1/automation/145_security_official_api_lsoa_validation.ps1' 'docs/chatgpt_status/aays1/runner_outputs/145_security_official_api_lsoa_validation.json'
    $result.child_steps += $step145
    if ($step145.blockers) { $result.blockers += @($step145.blockers | ForEach-Object { "145:$_" }) }
    $out145 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/145_security_official_api_lsoa_validation.json'
    if ($null -ne $out145) {
      $result.unique_lsoa_count = $out145.unique_lsoa_count
      $result.lsoa_http_200_count = $out145.lsoa_http_200_count
      $result.official_latest_month = $out145.official_latest_month
    }
    $apiPass = ($step145.exit_code -eq 0 -and $null -ne $out145 -and $out145.status -eq 'completed_all_lsoa_official_api_validated' -and $out145.lsoa_failed_count -eq 0 -and $out145.lsoa_http_200_count -eq $out145.unique_lsoa_count)
    if (-not $apiPass) { $result.blockers += 'all_lsoa_official_api_gate_not_passed' }

    if ($apiPass) {
      $step147 = Invoke-Child 'docs/chatgpt_status/aays1/automation/147_security_300_browser_validation.ps1' 'docs/chatgpt_status/aays1/runner_outputs/147_security_300_browser_validation.json'
      $result.child_steps += $step147
      if ($step147.blockers) { $result.blockers += @($step147.blockers | ForEach-Object { "147:$_" }) }
      $out147 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/147_security_300_browser_validation.json'
      if ($null -ne $out147) {
        $result.browser_300_status = $out147.browser_status
        $result.browser_latest_filter_rows = $out147.latest_filter_rows
        $result.console_error_count = $out147.console_error_count
      }
      $browserPass = ($step147.exit_code -eq 0 -and $null -ne $out147 -and $out147.browser_status -eq 'pass' -and $out147.console_error_count -eq 0 -and [string]$out147.latest_filter_rows -match '150\s+sat')
      if (-not $browserPass) { $result.blockers += '300_row_browser_gate_not_passed' }
      if ($browserPass) { $result.site_data_publish_allowed = $true }
    }
  }
}

if (-not $result.site_data_publish_allowed) {
  try {
    Push-Location $repoRoot
    & git fetch origin $branch 2>&1 | Out-Null
    & git restore --source "origin/$branch" -- @sitePaths 2>&1 | Out-Null
    $result.site_data_restored_after_blocker = ($LASTEXITCODE -eq 0)
    if (-not $result.site_data_restored_after_blocker) { $result.blockers += 'site_data_restore_failed_after_blocker' }
  } catch {
    $result.blockers += "site_data_restore_exception:$($_.Exception.Message)"
  } finally { try { Pop-Location } catch {} }
}

$result.status = if ($result.site_data_publish_allowed) {
  'ready_to_publish_300_verified_internet_validated_browser_pass'
} else {
  'blocked_before_atomic_site_publish'
}
$result | ConvertTo-Json -Depth 40 | Set-Content -Encoding UTF8 $outPath

try {
  Push-Location $repoRoot
  $stagePaths = New-Object System.Collections.Generic.List[string]
  foreach ($rel in $evidencePaths) { if (Test-Path (Join-Path $repoRoot $rel)) { $stagePaths.Add($rel) | Out-Null } }
  if ($result.site_data_publish_allowed) {
    foreach ($rel in $sitePaths) { if (Test-Path (Join-Path $repoRoot $rel)) { $stagePaths.Add($rel) | Out-Null } }
  }
  & git add -- @($stagePaths) 2>&1 | Out-Null
  $changes = @(& git status --porcelain -- @($stagePaths))
  if ($changes.Count -gt 0) {
    $message = if ($result.site_data_publish_allowed) { 'aays1 publish 300 strict Security rows with official API and browser proof' } else { 'aays1 record strict Security multiwork blocker evidence' }
    & git commit -m $message 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
      $result.commit_sha = (& git rev-parse HEAD).Trim()
      & git push origin $branch 2>&1 | Out-Null
      $result.git_push_status = if ($LASTEXITCODE -eq 0) { 'pushed' } else { 'push_failed' }
    } else { $result.git_push_status = 'commit_failed' }
  } else {
    $result.commit_sha = (& git rev-parse HEAD).Trim()
    $result.git_push_status = 'no_changes_to_push'
  }

  if ($result.git_push_status -in @('pushed','no_changes_to_push')) {
    & git fetch origin $branch 2>&1 | Out-Null
    if ($result.site_data_publish_allowed) {
      $remoteStatusText = (& git show "origin/$branch`:england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json" 2>$null) -join "`n"
      $remoteProofText = (& git show "origin/$branch`:docs/chatgpt_status/_shared/reports/security_300_rows_browser_validation_20260711.json" 2>$null) -join "`n"
      $statusOk = ($remoteStatusText -match '"verified_csv_rows"\s*:\s*300' -and $remoteStatusText -match 'official_api_lsoa_validated_count')
      $proofOk = ($remoteProofText -match '"status"\s*:\s*"pass"')
      $result.remote_readback_status = if ($statusOk -and $proofOk) { 'passed' } else { 'failed' }
      $result.site_data_published = ($result.remote_readback_status -eq 'passed')
      if (-not $result.site_data_published) { $result.blockers += 'remote_300_site_readback_failed' }
    } else {
      $result.remote_readback_status = 'blocker_evidence_pushed_site_data_not_published'
    }
  }
} catch {
  $result.git_push_status = 'exception'
  $result.remote_readback_status = 'exception'
  $result.blockers += "git_sync_exception:$($_.Exception.Message)"
} finally { try { Pop-Location } catch {} }

$result.status = if ($result.site_data_published) {
  'completed_300_verified_internet_validated_browser_pass_final_false'
} elseif ($result.site_data_publish_allowed) {
  'publish_attempt_failed_or_remote_readback_failed'
} else {
  'blocked_before_atomic_site_publish'
}
$result.final_ready = $false
$result.product_final_ready = $false
$result | ConvertTo-Json -Depth 40 | Set-Content -Encoding UTF8 $outPath

try {
  Push-Location $repoRoot
  & git add -- $outRel 2>&1 | Out-Null
  $outChanges = @(& git status --porcelain -- $outRel)
  if ($outChanges.Count -gt 0) {
    & git commit -m 'aays1 sync final 146 strict Security orchestrator status' 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { & git push origin $branch 2>&1 | Out-Null }
  }
} catch {} finally { try { Pop-Location } catch {} }

Write-Host "OUTPUT=$outPath"
if (-not $result.site_data_published -or $result.blockers.Count -gt 0) { exit 2 }
exit 0
