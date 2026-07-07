$ErrorActionPreference = "Stop"

$RepoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
}

$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { "aays1-065-product-evidence-implementation-20260708" } else { $env:AAYS_TASK_ID }
$PageKey = if ([string]::IsNullOrWhiteSpace($env:AAYS_PAGE_KEY)) { "aays1" } else { $env:AAYS_PAGE_KEY }
$TargetBranch = if ([string]::IsNullOrWhiteSpace($env:AAYS_TARGET_BRANCH)) { "codex/aays-single-runner-v5-20260706" } else { $env:AAYS_TARGET_BRANCH }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Now = (Get-Date).ToString("o")

$AaysRoot = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey"
$StatusDir = Join-Path $AaysRoot "status"
$ReportDir = Join-Path $AaysRoot "reports"
$HeartbeatDir = Join-Path $AaysRoot "heartbeat"
$RunnerOutDir = Join-Path $AaysRoot "runner_outputs"
$SecurityOutDir = Join-Path $RepoRoot "outputs\england_program_parcel_matrix_20260629\security_public_safety_updates"
New-Item -ItemType Directory -Force -Path $StatusDir,$ReportDir,$HeartbeatDir,$RunnerOutDir,$SecurityOutDir | Out-Null

function Write-JsonFile([string]$Path, $Object, [int]$Depth = 20) {
  ($Object | ConvertTo-Json -Depth $Depth) | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Write-Heartbeat([string]$State, [int]$Errors) {
  $line = "timestamp=$((Get-Date).ToString('o')) task_id=$TaskId page_key=$PageKey state=$State errors=$Errors final_ready=false fake_data=false db_write=false migration=false production_deploy=false"
  $line | Set-Content -LiteralPath (Join-Path $HeartbeatDir "aays1_065_product_evidence_heartbeat_latest.txt") -Encoding UTF8
}

$required = [ordered]@{
  batch_115_runner = "docs\chatgpt_status\security_public_safety\runner_outputs\115_security_batch_join_backoff.json"
  verified_geojson = "england_map_web\data\security_public_safety\parcel_security_scores_verified.geojson"
  verified_csv = "england_map_web\data\security_public_safety\parcel_security_scores_verified.csv"
  manifest = "england_map_web\data\security_public_safety\security_evidence_manifest.json"
  latest_changes = "outputs\england_program_parcel_matrix_20260629\security_public_safety_updates\latest_changes.json"
}

$errors = New-Object System.Collections.ArrayList
$warnings = New-Object System.Collections.ArrayList
$evidence = New-Object System.Collections.ArrayList
Write-Heartbeat "started" 0

foreach ($k in $required.Keys) {
  $rel = $required[$k]
  $path = Join-Path $RepoRoot $rel
  if (-not (Test-Path -LiteralPath $path)) {
    [void]$errors.Add([ordered]@{ artifact=$k; path=$rel; error="missing_required_artifact" })
  } else {
    [void]$evidence.Add([ordered]@{ artifact=$k; path=$rel; exists=$true })
  }
}

$batch = $null
$manifest = $null
$latest = $null
$csvRows = @()
$geoFeatureCount = 0

try {
  if ($errors.Count -eq 0) {
    $batch = Get-Content -LiteralPath (Join-Path $RepoRoot $required["batch_115_runner"]) -Raw | ConvertFrom-Json
    $manifest = Get-Content -LiteralPath (Join-Path $RepoRoot $required["manifest"]) -Raw | ConvertFrom-Json
    $latest = Get-Content -LiteralPath (Join-Path $RepoRoot $required["latest_changes"]) -Raw | ConvertFrom-Json
    $csvRows = @(Import-Csv -LiteralPath (Join-Path $RepoRoot $required["verified_csv"]))
    $geo = Get-Content -LiteralPath (Join-Path $RepoRoot $required["verified_geojson"]) -Raw | ConvertFrom-Json
    $geoFeatureCount = @($geo.features).Count

    if ($batch.status -ne "completed") { [void]$errors.Add([ordered]@{ artifact="batch_115_runner"; error="batch_status_not_completed"; value=$batch.status }) }
    if ([int]$batch.verified_new_rows -lt 150) { [void]$errors.Add([ordered]@{ artifact="batch_115_runner"; error="verified_new_rows_below_150"; value=$batch.verified_new_rows }) }
    if ($batch.fake_data -eq $true) { [void]$errors.Add([ordered]@{ artifact="batch_115_runner"; error="fake_data_true" }) }
    if ($manifest.fake_data -eq $true) { [void]$errors.Add([ordered]@{ artifact="manifest"; error="fake_data_true" }) }
    if ([int]$manifest.selected_verified_rows -lt 150) { [void]$errors.Add([ordered]@{ artifact="manifest"; error="selected_verified_rows_below_150"; value=$manifest.selected_verified_rows }) }
    if (@($csvRows).Count -lt 150) { [void]$errors.Add([ordered]@{ artifact="verified_csv"; error="csv_rows_below_150"; value=@($csvRows).Count }) }
    if ($geoFeatureCount -lt 150) { [void]$errors.Add([ordered]@{ artifact="verified_geojson"; error="geojson_features_below_150"; value=$geoFeatureCount }) }
    if ($manifest.source_summary -eq $null) { [void]$warnings.Add([ordered]@{ artifact="manifest"; warning="source_summary_null_real_source_trace_expansion_still_needed" }) }
  }
} catch {
  [void]$errors.Add([ordered]@{ artifact="parser"; error=$_.Exception.Message })
}

$ok = ($errors.Count -eq 0)
$statusText = if ($ok) { "completed_evidence_verified_pending_browser_final" } else { "blocked_evidence_validation_failed" }
$overallPercent = if ($ok) { 42 } else { 35 }

$result = [ordered]@{
  task_id = $TaskId
  page_key = $PageKey
  layer = "Safety / Security"
  program_output = "Security Level percent"
  status = $statusText
  checked_at = (Get-Date).ToString("o")
  target_branch = $TargetBranch
  required_artifacts = $evidence
  verified_csv_rows = @($csvRows).Count
  verified_geojson_features = $geoFeatureCount
  batch_115_status = if ($batch) { $batch.status } else { $null }
  batch_115_verified_new_rows = if ($batch) { [int]$batch.verified_new_rows } else { $null }
  batch_115_accuracy_ge_3_count = if ($batch) { [int]$batch.accuracy_ge_3_count } else { $null }
  manifest_selected_verified_rows = if ($manifest) { [int]$manifest.selected_verified_rows } else { $null }
  latest_changes_status = if ($latest) { $latest.status } else { $null }
  overall_progress_percent = $overallPercent
  progress_delta_percent = if ($ok) { 7 } else { 0 }
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  person_level_data = $false
  warnings = $warnings
  errors = $errors
  blockers = if ($ok) { @("browser_smoke_and_popup_right_panel_proof_required_before_final_ready", "source_summary_null_requires_follow_up_if_full_source_trace_required") } else { @("required_security_public_safety_artifact_missing_or_invalid") }
}

Write-JsonFile -Path (Join-Path $RunnerOutDir "aays1_065_product_evidence_summary.json") -Object $result -Depth 30
Write-JsonFile -Path (Join-Path $StatusDir "aays1_065_product_evidence_latest.json") -Object $result -Depth 30

if ($ok) {
  $siteStatus = [ordered]@{
    page_key = $PageKey
    task_id = $TaskId
    checked_at = (Get-Date).ToString("o")
    status = "aays1_065_product_evidence_verified_pending_browser_final"
    user_visible_summary = "Safety / Security verified batch 115 artifacts were validated by the aays1 065 implementation. Product final remains false until browser layer and popup/right-panel proof exists."
    layer = "Safety / Security"
    program_output = "Security Level percent"
    verified_csv_rows = @($csvRows).Count
    verified_geojson_features = $geoFeatureCount
    site_visible_outputs = @(
      "docs/chatgpt_status/aays1/status/aays1_065_product_evidence_latest.json",
      "docs/chatgpt_status/aays1/reports/aays1_065_product_evidence_report.md",
      "docs/chatgpt_status/aays1/heartbeat/aays1_065_product_evidence_heartbeat_latest.txt",
      "docs/chatgpt_status/aays1/runner_outputs/aays1_065_product_evidence_summary.json",
      "outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json"
    )
    completed = $true
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    needs_browser_smoke_proof = $true
  }
  Write-JsonFile -Path (Join-Path $StatusDir "aays1_site_visible_current_status_latest.json") -Object $siteStatus -Depth 20

  $securityLatest = [ordered]@{
    layer = "Safety / Security"
    program_output = "Security Level percent"
    status = "AAYS1_065_EVIDENCE_VERIFIED_PENDING_BROWSER_FINAL"
    last_updated = (Get-Date).ToString("o")
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration_apply = $false
    prod_deploy = $false
    verified_csv_rows = @($csvRows).Count
    verified_geojson_features = $geoFeatureCount
    accuracy_ge_3_count = if ($batch) { [int]$batch.accuracy_ge_3_count } else { 0 }
    source_note = "Validated existing Security/Public Safety batch 115 artifacts; no fake rows added by aays1 065 task."
    expected_output_files = @(
      "england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson",
      "england_map_web/data/security_public_safety/parcel_security_scores_verified.csv",
      "england_map_web/data/security_public_safety/security_evidence_manifest.json"
    )
    blockers = @(
      "browser smoke proof required for Security layer button, thematic colors, legend, popup/right-panel fields",
      "final_ready remains false"
    )
  }
  Write-JsonFile -Path (Join-Path $SecurityOutDir "latest_changes.json") -Object $securityLatest -Depth 20
}

$reportLines = @()
$reportLines += "# AAYS1 065 Product Evidence Report"
$reportLines += ""
$reportLines += "status=$statusText"
$reportLines += "task_id=$TaskId"
$reportLines += "page_key=$PageKey"
$reportLines += "layer=Safety / Security"
$reportLines += "program_output=Security Level percent"
$reportLines += "verified_csv_rows=$(@($csvRows).Count)"
$reportLines += "verified_geojson_features=$geoFeatureCount"
$reportLines += "batch_115_verified_new_rows=$(if ($batch) { [int]$batch.verified_new_rows } else { 0 })"
$reportLines += "manifest_selected_verified_rows=$(if ($manifest) { [int]$manifest.selected_verified_rows } else { 0 })"
$reportLines += "overall_progress_percent=$overallPercent"
$reportLines += "progress_delta_percent=$(if ($ok) { 7 } else { 0 })"
$reportLines += "final_ready=false"
$reportLines += "product_final_ready=false"
$reportLines += "fake_data=false"
$reportLines += "db_write=false"
$reportLines += "migration=false"
$reportLines += "production_deploy=false"
$reportLines += ""
if ($warnings.Count -gt 0) {
  $reportLines += "## Warnings"
  foreach ($w in $warnings) { $reportLines += "- $($w.warning) [$($w.artifact)]" }
  $reportLines += ""
}
if ($errors.Count -gt 0) {
  $reportLines += "## Errors"
  foreach ($e in $errors) { $reportLines += "- $($e.error) [$($e.artifact)]" }
  $reportLines += ""
}
$reportLines += "## Next blocker"
$reportLines += "Browser smoke and popup/right-panel proof are still required before final_ready=true."
$reportLines | Set-Content -LiteralPath (Join-Path $ReportDir "aays1_065_product_evidence_report.md") -Encoding UTF8

Write-Heartbeat $statusText $errors.Count

if ($ok) {
  Write-Output "AAYS1_065_PRODUCT_EVIDENCE_VERIFIED task_id=$TaskId verified_csv_rows=$(@($csvRows).Count) verified_geojson_features=$geoFeatureCount final_ready=false fake_data=false db_write=false migration=false production_deploy=false"
} else {
  Write-Output "AAYS1_065_PRODUCT_EVIDENCE_BLOCKED task_id=$TaskId errors=$($errors.Count) final_ready=false fake_data=false db_write=false migration=false production_deploy=false"
}
exit 0
