$ErrorActionPreference = 'Continue'
$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$outDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/runner_outputs'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outPath = Join-Path $outDir '104_visible_expansion_orchestrator.json'

$scripts = @(
  'docs/chatgpt_status/aays1/automation/102_real_visible_security_site_bridge.ps1',
  'docs/chatgpt_status/aays1/automation/103_security_accuracy_count_expansion.ps1'
)
$results = @()
foreach ($rel in $scripts) {
  $p = Join-Path $repoRoot $rel
  $item = [ordered]@{ script=$rel; exists=(Test-Path $p); exit_code=$null; status='not_run' }
  if (Test-Path $p) {
    try {
      & powershell -NoProfile -ExecutionPolicy Bypass -File $p
      $item.exit_code = $LASTEXITCODE
      $item.status = if ($LASTEXITCODE -eq 0) { 'completed' } else { 'completed_with_blocker_or_nonzero_exit' }
    } catch {
      $item.status = 'exception'
      $item.error = $_.Exception.Message
    }
  }
  $results += [pscustomobject]$item
}

$expected = @(
  'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json',
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson',
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv',
  'england_map_web/data/security_public_safety/security_evidence_manifest.json',
  'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json',
  'docs/chatgpt_status/aays1/runner_outputs/102_real_visible_security_site_bridge.json',
  'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json',
  'docs/chatgpt_status/aays1/runner_outputs/104_visible_expansion_orchestrator.json'
)
function Get-ExpectedOutputs {
  $outs = @()
  foreach ($rel in $expected) {
    $p = Join-Path $repoRoot $rel
    $outs += [pscustomobject]@{ path=$rel; exists=(Test-Path $p) }
  }
  return $outs
}
function New-Result([object]$gitSync, [string]$statusText) {
  return [ordered]@{
    task_id='aays1-104-visible-expansion-orchestrator-20260709'
    page_key='aays1'
    status=$statusText
    checked_at=(Get-Date).ToString('o')
    repo_root=$repoRoot
    canonical_storage='F_PORTABLE_ROOT'
    single_runner_only=$true
    parallel_runner=$false
    scripts=$results
    expected_outputs=(Get-ExpectedOutputs)
    git_sync=$gitSync
    final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
    person_level_data=$false
    blockers=@('browser_smoke_required_before_final_ready')
  }
}

$gitSync = [ordered]@{
  attempted=$true
  status='pre_output_written_before_git_add'
  first_push_exit_code=$null
  first_push_status='not_attempted'
  second_status_push_status='not_attempted'
  changed_count=$null
  stdout=@()
  stderr=@()
}

# Critical fix: write 104 output BEFORE git add/commit/push so this file can be committed.
$preResult = New-Result $gitSync 'pre_sync_output_written_pending_git_push'
$preResult | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $outPath

try {
  Push-Location $repoRoot
  & git add -- @($expected) 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ }
  $changes = & git status --porcelain
  $gitSync.changed_count = @($changes).Count
  if (@($changes).Count -gt 0) {
    & git commit -m 'aays1 sync visible expansion runner outputs' 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ }
    $commitExit = $LASTEXITCODE
    if ($commitExit -eq 0) {
      & git push 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ }
      $gitSync.first_push_exit_code = $LASTEXITCODE
      $gitSync.first_push_status = if ($LASTEXITCODE -eq 0) { 'pushed' } else { 'push_failed' }
    } else {
      $gitSync.first_push_exit_code = $commitExit
      $gitSync.first_push_status = 'commit_failed'
    }
  } else {
    $gitSync.first_push_exit_code = 0
    $gitSync.first_push_status = 'no_changes_to_push'
  }

  $finalResult = New-Result $gitSync 'completed_orchestrator_attempt_pending_browser_smoke'
  $finalResult | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $outPath
  & git add -- 'docs/chatgpt_status/aays1/runner_outputs/104_visible_expansion_orchestrator.json' 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ }
  $statusChanges = & git status --porcelain -- 'docs/chatgpt_status/aays1/runner_outputs/104_visible_expansion_orchestrator.json'
  if (@($statusChanges).Count -gt 0) {
    & git commit -m 'aays1 sync 104 orchestrator status after push' 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ }
    if ($LASTEXITCODE -eq 0) {
      & git push 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ }
      $gitSync.second_status_push_status = if ($LASTEXITCODE -eq 0) { 'pushed_status_file' } else { 'status_push_failed' }
    } else {
      $gitSync.second_status_push_status = 'status_commit_failed'
    }
  } else {
    $gitSync.second_status_push_status = 'no_status_change_to_push'
  }
} catch {
  $gitSync.first_push_status = 'exception'
  $gitSync.stderr += $_.Exception.Message
} finally {
  try { Pop-Location } catch {}
}

# Keep local final copy with the latest sync attempt details.
$finalResult = New-Result $gitSync 'completed_orchestrator_attempt_pending_browser_smoke'
$finalResult | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $outPath
Write-Host "OUTPUT=$outPath"
exit 0
