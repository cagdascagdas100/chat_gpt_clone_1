$ErrorActionPreference = 'Continue'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$branch = 'codex/aays-single-runner-v5-20260706'
$outDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/runner_outputs'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outPath = Join-Path $outDir '104_visible_expansion_orchestrator.json'
$outRel = 'docs/chatgpt_status/aays1/runner_outputs/104_visible_expansion_orchestrator.json'

$scripts = @(
  'docs/chatgpt_status/aays1/automation/103_security_accuracy_count_expansion.ps1',
  'docs/chatgpt_status/aays1/automation/142_security_site_row_evidence_visibility_fix.ps1'
)

$expected = @(
  'england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json',
  'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json',
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson',
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv',
  'england_map_web/data/security_public_safety/security_evidence_manifest.json',
  'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json',
  'docs/chatgpt_status/aays1/reports/137_security_verified_expansion_latest.md',
  'docs/chatgpt_status/aays1/reports/142_security_site_row_evidence_visibility_fix_completion_20260711.md',
  'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json',
  'docs/chatgpt_status/aays1/runner_outputs/142_security_site_row_evidence_visibility_fix.json',
  'docs/chatgpt_status/_shared/reports/security_row_evidence_browser_validation_20260711.json',
  $outRel
)

function Read-JsonIfExists([string]$rel) {
  $p = Join-Path $repoRoot $rel
  if (-not (Test-Path $p)) { return $null }
  try { return Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json } catch { return $null }
}

function Get-ExpectedOutputs {
  $items = @()
  foreach ($rel in $expected) {
    $p = Join-Path $repoRoot $rel
    $items += [pscustomobject]@{ path=$rel; exists=(Test-Path $p); size_bytes=if(Test-Path $p){(Get-Item $p).Length}else{$null} }
  }
  return $items
}

$result = [ordered]@{
  task_id = 'aays1-137-next-batch-source-fetch-20260710'
  orchestrator_id = 'aays1-104-visible-expansion-orchestrator-20260709'
  implementation = 'strict_expansion_then_browser_validation_v2'
  page_key = 'aays1'
  status = 'started'
  checked_at = (Get-Date).ToString('o')
  repo_root = $repoRoot
  branch = $branch
  canonical_storage = 'F_PORTABLE_ROOT'
  single_runner_only = $true
  parallel_runner = $false
  child_scripts = @()
  expected_outputs = @()
  before_verified_rows = $null
  after_verified_rows = $null
  added_rows = $null
  score_4_count = $null
  manual_review_count = $null
  browser_smoke_status = $null
  console_error_count = $null
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

$baselineStatus = Read-JsonIfExists 'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json'
if ($null -ne $baselineStatus) { $result.before_verified_rows = $baselineStatus.verified_csv_rows }

foreach ($rel in $scripts) {
  $p = Join-Path $repoRoot $rel
  $item = [ordered]@{ script=$rel; exists=(Test-Path $p); exit_code=$null; status='not_run'; output=$null }
  if (-not (Test-Path $p)) {
    $item.status = 'missing_script'
    $result.blockers += "missing_script:$rel"
    $result.child_scripts += [pscustomobject]$item
    continue
  }
  try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $p
    $item.exit_code = $LASTEXITCODE
    $item.status = if ($LASTEXITCODE -eq 0) { 'completed' } else { 'completed_with_blocker_or_nonzero_exit' }
  } catch {
    $item.status = 'exception'
    $item.error = $_.Exception.Message
    $result.blockers += "child_exception:$rel:$($_.Exception.Message)"
  }
  if ($rel -match '103_security_accuracy') {
    $child = Read-JsonIfExists 'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json'
    if ($null -ne $child) {
      $item.output = $child.status
      $result.after_verified_rows = $child.selected_count
      $result.added_rows = $child.added_count
      $result.score_4_count = $child.score_4_count
      $result.manual_review_count = $child.manual_review_count
      if ($child.blockers) { $result.blockers += @($child.blockers | ForEach-Object { "103:$_" }) }
    } else { $result.blockers += 'missing_103_runner_output' }
  }
  if ($rel -match '142_security_site') {
    $child = Read-JsonIfExists 'docs/chatgpt_status/aays1/runner_outputs/142_security_site_row_evidence_visibility_fix.json'
    if ($null -ne $child) {
      $item.output = $child.status
      $result.browser_smoke_status = $child.browser_smoke_status
      $result.console_error_count = $child.console_error_count
      if ($child.blockers) { $result.blockers += @($child.blockers | ForEach-Object { "142:$_" }) }
    } else { $result.blockers += 'missing_142_runner_output_after_expansion' }
  }
  $result.child_scripts += [pscustomobject]$item
}

$result.expected_outputs = Get-ExpectedOutputs
$missingExpected = @($result.expected_outputs | Where-Object { -not $_.exists })
if ($missingExpected.Count -gt 0) { $result.blockers += @($missingExpected | ForEach-Object { "missing_expected:$($_.path)" }) }

if ($null -eq $result.after_verified_rows) {
  $statusAfter = Read-JsonIfExists 'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json'
  if ($null -ne $statusAfter) { $result.after_verified_rows = $statusAfter.verified_csv_rows }
}
if ($null -eq $result.added_rows -and $null -ne $result.after_verified_rows -and $null -ne $result.before_verified_rows) {
  $result.added_rows = [int]$result.after_verified_rows - [int]$result.before_verified_rows
}

$result.status = if ($result.blockers.Count -eq 0 -and $result.after_verified_rows -ge 300 -and $result.browser_smoke_status -eq 'pass' -and $result.console_error_count -eq 0) {
  'completed_300_verified_rows_browser_pass_pending_product_final_gate'
} elseif ($result.after_verified_rows -ge 300) {
  'expanded_300_rows_with_browser_or_proof_blocker'
} else {
  'blocked_before_300_verified_rows'
}

$result | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $outPath

try {
  Push-Location $repoRoot
  & git add -- @($expected) 2>&1 | Out-Null
  $changes = @(& git status --porcelain -- @($expected))
  if ($changes.Count -gt 0) {
    & git commit -m 'aays1 sync strict security expansion and browser proof' 2>&1 | Out-Null
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
    $remoteStatus = & git show "origin/$branch`:england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json" 2>$null
    $remoteOutput = & git show "origin/$branch`:$outRel" 2>$null
    $statusOk = ($LASTEXITCODE -eq 0 -and ($remoteStatus -join "`n") -match 'verified_csv_rows')
    $outputOk = (($remoteOutput -join "`n") -match 'orchestrator_id')
    $result.remote_readback_status = if ($statusOk -and $outputOk) { 'passed' } else { 'failed' }
  }
} catch {
  $result.git_push_status = 'exception'
  $result.remote_readback_status = 'exception'
  $result.blockers += "git_sync_exception:$($_.Exception.Message)"
} finally { try { Pop-Location } catch {} }

$result | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $outPath

try {
  Push-Location $repoRoot
  & git add -- $outRel 2>&1 | Out-Null
  $statusChanges = @(& git status --porcelain -- $outRel)
  if ($statusChanges.Count -gt 0) {
    & git commit -m 'aays1 sync final 104 orchestrator status' 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { & git push origin $branch 2>&1 | Out-Null }
  }
} catch { $result.blockers += "final_output_push_exception:$($_.Exception.Message)" } finally { try { Pop-Location } catch {} }

$result | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $outPath
Write-Host "OUTPUT=$outPath"
if ($result.blockers.Count -gt 0 -or $result.after_verified_rows -lt 300 -or $result.browser_smoke_status -ne 'pass') { exit 2 }
exit 0
