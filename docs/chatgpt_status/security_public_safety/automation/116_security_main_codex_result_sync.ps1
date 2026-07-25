$ErrorActionPreference = 'Stop'

$Repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($Repo)) {
  try { $Repo = (git rev-parse --show-toplevel).Trim() } catch { $Repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path }
}

$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { 'security-main-codex-result-sync-verify-20260708-001' } else { $env:AAYS_TASK_ID }
$PageKey = 'aays1'
$LayerKey = 'security_public_safety'
$SourceBranchName = 'codex/aays-single-runner-v5-20260706'
$SourceRef = "origin/$SourceBranchName"
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Now = (Get-Date).ToString('o')

$LayerRoot = Join-Path $Repo "docs\chatgpt_status\$LayerKey"
$AaysRoot = Join-Path $Repo "docs\chatgpt_status\$PageKey"
$OutDir = Join-Path $LayerRoot 'runner_outputs'
$StatusDir = Join-Path $LayerRoot 'status'
$ReportDir = Join-Path $LayerRoot 'reports'
$AaysStatusDir = Join-Path $AaysRoot 'status'
$DataDir = Join-Path $Repo 'england_map_web\data\security_public_safety'
$LatestDir = Join-Path $Repo 'outputs\england_program_parcel_matrix_20260629\security_public_safety_updates'
New-Item -ItemType Directory -Force -Path $OutDir,$StatusDir,$ReportDir,$AaysStatusDir,$DataDir,$LatestDir | Out-Null

function Write-JsonFile([string]$Path, $Object, [int]$Depth = 20) {
  ($Object | ConvertTo-Json -Depth $Depth) | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Write-Heartbeat([string]$Status, [int]$Copied, [int]$Errors) {
  Write-JsonFile -Path (Join-Path $AaysStatusDir 'runner-heartbeat-latest.json') -Object ([ordered]@{
    page_key = $PageKey
    layer = $LayerKey
    task_id = $TaskId
    status = $Status
    timestamp = (Get-Date).ToString('o')
    copied_artifacts = $Copied
    error_count = $Errors
    final_ready = $false
    fake_data = $false
  }) -Depth 10
}

$relativePaths = [ordered]@{
  runner_output = 'docs/chatgpt_status/security_public_safety/runner_outputs/115_security_batch_join_backoff.json'
  verified_geojson = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson'
  verified_csv = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv'
  manifest = 'england_map_web/data/security_public_safety/security_evidence_manifest.json'
  latest_changes = 'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json'
}

$errors = New-Object System.Collections.ArrayList
$copied = New-Object System.Collections.ArrayList
$artifactTexts = @{}
Write-Heartbeat 'security_116_main_codex_sync_started' 0 0

try {
  Push-Location $Repo

  $fetchOk = $true
  try {
    git fetch origin $SourceBranchName --depth=1 2>$null | Out-Null
  } catch {
    try { git fetch origin $SourceBranchName 2>$null | Out-Null } catch { $fetchOk = $false; [void]$errors.Add([ordered]@{ step='git_fetch'; error=$_.Exception.Message }) }
  }

  if (-not $fetchOk) { throw 'Source branch fetch failed; cannot verify codex batch 115 artifacts.' }

  foreach ($name in $relativePaths.Keys) {
    $rel = $relativePaths[$name]
    try {
      $text = git show "$SourceRef`:$rel" 2>$null
      if ([string]::IsNullOrWhiteSpace(($text -join "`n"))) { throw "Empty artifact: $rel" }
      $artifactTexts[$name] = ($text -join "`n")
    } catch {
      [void]$errors.Add([ordered]@{ step='git_show'; artifact=$name; path=$rel; error=$_.Exception.Message })
    }
  }

  if ($errors.Count -gt 0) { throw 'One or more source artifacts are missing or unreadable.' }

  $sourceRunner = $artifactTexts['runner_output'] | ConvertFrom-Json
  if ($sourceRunner.status -ne 'completed') { throw "Source runner output is not completed: $($sourceRunner.status)" }
  if ([int]$sourceRunner.verified_new_rows -lt 150) { throw "Source verified_new_rows is below 150: $($sourceRunner.verified_new_rows)" }
  if ($sourceRunner.fake_data -eq $true) { throw 'Source runner output is marked fake_data=true; refusing sync.' }
  if ($sourceRunner.final_ready -eq $true -or $sourceRunner.product_final_ready -eq $true) { throw 'Source unexpectedly claims final_ready=true; refusing sync until browser proof is checked.' }

  $sourceManifest = $artifactTexts['manifest'] | ConvertFrom-Json
  if ($sourceManifest.fake_data -eq $true) { throw 'Source manifest is marked fake_data=true; refusing sync.' }
  if ($sourceManifest.final_ready -eq $true) { throw 'Source manifest claims final_ready=true; refusing sync until browser proof is checked.' }

  $writeMap = [ordered]@{
    verified_geojson = Join-Path $Repo $relativePaths['verified_geojson'].Replace('/','\')
    verified_csv = Join-Path $Repo $relativePaths['verified_csv'].Replace('/','\')
    manifest = Join-Path $Repo $relativePaths['manifest'].Replace('/','\')
  }

  foreach ($name in $writeMap.Keys) {
    $dest = $writeMap[$name]
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
    $artifactTexts[$name] | Set-Content -LiteralPath $dest -Encoding UTF8
    [void]$copied.Add([ordered]@{ artifact=$name; path=$relativePaths[$name] })
  }

  $csvRows = @(Import-Csv -LiteralPath $writeMap['verified_csv'])
  $geo = Get-Content -LiteralPath $writeMap['verified_geojson'] -Raw | ConvertFrom-Json
  $geoCount = @($geo.features).Count

  $latest = $artifactTexts['latest_changes'] | ConvertFrom-Json
  $latest.status = 'MAIN_SYNCED_FROM_CODEX_BATCH_115_PENDING_BROWSER_SMOKE'
  $latest.last_updated = (Get-Date).ToString('o')
  $latest.final_ready = $false
  $latest.fake_data = $false
  $latest | Add-Member -Force -NotePropertyName sync_task_id -NotePropertyValue $TaskId
  $latest | Add-Member -Force -NotePropertyName sync_source_branch -NotePropertyValue $SourceBranchName
  $latest | Add-Member -Force -NotePropertyName synced_verified_csv_rows -NotePropertyValue @($csvRows).Count
  $latest | Add-Member -Force -NotePropertyName synced_verified_geojson_features -NotePropertyValue $geoCount
  $latest.blockers = @(
    'browser smoke proof required for Security button, parcel thematic colors, legend, popup/right-panel fields',
    'final_ready must remain false until site-visible layer proof exists',
    'AAYS1 065 real source/evidence fetch implementation remains separate broader blocker if continuing aays1 recovery'
  )
  Write-JsonFile -Path (Join-Path $LatestDir 'latest_changes.json') -Object $latest -Depth 30

  $status = [ordered]@{
    task_id = $TaskId
    page_key = $PageKey
    layer = $LayerKey
    status = 'completed'
    completed_at = (Get-Date).ToString('o')
    source_branch = $SourceBranchName
    copied_artifacts = $copied
    verified_csv_rows = @($csvRows).Count
    verified_geojson_features = $geoCount
    source_verified_new_rows = [int]$sourceRunner.verified_new_rows
    source_accuracy_ge_3_count = [int]$sourceRunner.accuracy_ge_3_count
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    blockers = @('browser_smoke_and_popup_right_panel_proof_required_before_final_ready')
  }
  Write-JsonFile -Path (Join-Path $OutDir '116_security_main_codex_result_sync.json') -Object $status -Depth 30
  Write-JsonFile -Path (Join-Path $StatusDir '116_security_main_codex_result_sync.status.json') -Object $status -Depth 30
  Write-JsonFile -Path (Join-Path $AaysStatusDir "$TaskId`_completed.json") -Object $status -Depth 30

  @"
# Security 116 main/codex result sync

status=completed
task_id=$TaskId
source_branch=$SourceBranchName
verified_csv_rows=$(@($csvRows).Count)
verified_geojson_features=$geoCount
source_verified_new_rows=$([int]$sourceRunner.verified_new_rows)
source_accuracy_ge_3_count=$([int]$sourceRunner.accuracy_ge_3_count)
fake_data=false
final_ready=false
blocker=browser_smoke_and_popup_right_panel_proof_required_before_final_ready
"@ | Set-Content -LiteralPath (Join-Path $ReportDir '116_security_main_codex_result_sync.md') -Encoding UTF8

  Write-Heartbeat 'security_116_main_codex_sync_completed' $copied.Count 0
  Write-Output "SECURITY_116_MAIN_CODEX_SYNC_COMPLETE task_id=$TaskId verified_csv_rows=$(@($csvRows).Count) verified_geojson_features=$geoCount final_ready=false fake_data=false"
  exit 0
}
catch {
  [void]$errors.Add([ordered]@{ step='fatal'; error=$_.Exception.Message })
  $blocked = [ordered]@{
    task_id = $TaskId
    page_key = $PageKey
    layer = $LayerKey
    status = 'blocked'
    blocked_at = (Get-Date).ToString('o')
    source_branch = $SourceBranchName
    errors = $errors
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    blockers = @('source_branch_artifacts_unavailable_or_failed_validation')
  }
  Write-JsonFile -Path (Join-Path $OutDir '116_security_main_codex_result_sync.json') -Object $blocked -Depth 30
  Write-JsonFile -Path (Join-Path $StatusDir '116_security_main_codex_result_sync.status.json') -Object $blocked -Depth 30
  Write-JsonFile -Path (Join-Path $AaysStatusDir "$TaskId`_blocked.json") -Object $blocked -Depth 30
  Write-JsonFile -Path (Join-Path $LatestDir 'latest_changes.json') -Object ([ordered]@{
    layer = 'Safety / Security'
    program_output = 'Security Level percent'
    status = 'TASK_116_BLOCKED_SOURCE_BRANCH_ARTIFACTS_MISSING_OR_INVALID'
    last_updated = (Get-Date).ToString('o')
    final_ready = $false
    fake_data = $false
    task_id = $TaskId
    source_branch = $SourceBranchName
    blockers = @('source branch artifacts unavailable or failed validation', 'do not fabricate security rows')
    errors = $errors
  }) -Depth 30
  @"
# Security 116 main/codex result sync

status=blocked
task_id=$TaskId
source_branch=$SourceBranchName
fake_data=false
final_ready=false
blocker=source_branch_artifacts_unavailable_or_failed_validation
"@ | Set-Content -LiteralPath (Join-Path $ReportDir '116_security_main_codex_result_sync.md') -Encoding UTF8
  Write-Heartbeat 'security_116_main_codex_sync_blocked' $copied.Count $errors.Count
  Write-Output "SECURITY_116_MAIN_CODEX_SYNC_BLOCKED task_id=$TaskId final_ready=false fake_data=false"
  exit 0
}
finally {
  try { Pop-Location } catch {}
}
