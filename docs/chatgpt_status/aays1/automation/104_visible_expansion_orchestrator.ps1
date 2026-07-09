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
  'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json'
)
$outputs = @()
foreach ($rel in $expected) {
  $p = Join-Path $repoRoot $rel
  $outputs += [pscustomobject]@{ path=$rel; exists=(Test-Path $p) }
}

$result = [ordered]@{
  task_id='aays1-104-visible-expansion-orchestrator-20260709'
  page_key='aays1'
  status='completed_orchestrator_attempt_pending_browser_smoke'
  checked_at=(Get-Date).ToString('o')
  repo_root=$repoRoot
  canonical_storage='F_PORTABLE_ROOT'
  single_runner_only=$true
  parallel_runner=$false
  scripts=$results
  expected_outputs=$outputs
  final_ready=$false
  fake_data=$false
  db_write=$false
  migration=$false
  production_deploy=$false
  person_level_data=$false
  blockers=@('browser_smoke_required_before_final_ready')
}
$result | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $outPath
Write-Host "OUTPUT=$outPath"
exit 0
