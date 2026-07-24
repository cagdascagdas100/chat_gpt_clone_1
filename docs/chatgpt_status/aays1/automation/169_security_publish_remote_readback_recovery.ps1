$ErrorActionPreference = 'Stop'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel).Trim() }
$branch = if ($env:AAYS_TARGET_BRANCH) { $env:AAYS_TARGET_BRANCH } else { 'codex/aays-single-runner-v5-20260706' }
$taskId = 'aays1-137-next-batch-source-fetch-20260710'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/169_security_publish_remote_readback_recovery.json'
$statusRel = 'docs/chatgpt_status/aays1/status/169_security_publish_remote_readback_recovery_latest.json'
$statusRelWeb = 'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json'
$rowsRel = 'england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json'
$csvRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv'
$geoRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson'
$proofRel = 'docs/chatgpt_status/_shared/reports/security_300_rows_browser_validation_20260711.json'

function Read-JsonFile([string]$Relative) {
  $path = Join-Path $repoRoot ($Relative -replace '/', '\')
  $text = [IO.File]::ReadAllText($path,[Text.Encoding]::UTF8).TrimStart([char]0xFEFF)
  return ($text | ConvertFrom-Json)
}
function Read-GitJson([string]$Relative) {
  $text = ((& git -C $repoRoot show ("origin/$branch`:$Relative") 2>$null) -join "`n").TrimStart([char]0xFEFF)
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($text)) { throw "remote_read_failed:$Relative" }
  return ($text | ConvertFrom-Json)
}
function Get-RowCount($Value) {
  if ($null -eq $Value) { return 0 }
  if ($null -ne $Value.rows) { return @($Value.rows).Count }
  if ($null -ne $Value.results) { return @($Value.results).Count }
  return @($Value).Count
}
function Write-Json([string]$Relative,[object]$Value) {
  $path = Join-Path $repoRoot ($Relative -replace '/', '\')
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
  [IO.File]::WriteAllText($path,($Value | ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
}

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$blockers = [Collections.Generic.List[string]]::new()
$status = Read-JsonFile $statusRelWeb
$rows = Read-JsonFile $rowsRel
$geo = Read-JsonFile $geoRel
$proof = Read-JsonFile $proofRel
$csvCount = @(Import-Csv -LiteralPath (Join-Path $repoRoot ($csvRel -replace '/', '\'))).Count
$rowCount = Get-RowCount $rows
$geoCount = @($geo.features).Count

if ([int]$status.verified_csv_rows -ne 300) { $blockers.Add('local_status_csv_not_300') }
if ([int]$status.verified_geojson_features -ne 300) { $blockers.Add('local_status_geojson_not_300') }
if ([int]$status.browser_visible_rows -ne 300) { $blockers.Add('local_status_browser_not_300') }
if ([int]$status.new_rows_in_latest_batch -ne 150) { $blockers.Add('local_status_new_rows_not_150') }
if ($csvCount -ne 300) { $blockers.Add("local_csv_count_$csvCount") }
if ($rowCount -ne 300) { $blockers.Add("local_visible_rows_count_$rowCount") }
if ($geoCount -ne 300) { $blockers.Add("local_geojson_count_$geoCount") }
if ([string]$proof.status -ne 'pass') { $blockers.Add('local_browser_proof_not_pass') }
if ([int]$proof.console_error_count -ne 0) { $blockers.Add('local_browser_console_errors') }
if (-not ([string]$proof.latest_filter_rows -match '150\s+sat')) { $blockers.Add('local_latest_filter_not_150') }

$remoteStatus = $null
$remoteProof = $null
try {
  $oldFetchEap = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    & git -C $repoRoot fetch --no-tags origin $branch 2>&1 | Out-Null
    $fetchCode = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $oldFetchEap
  }
  if ($fetchCode -ne 0) { throw "remote_fetch_failed_exit_$fetchCode" }
  $remoteStatus = Read-GitJson $statusRelWeb
  $remoteProof = Read-GitJson $proofRel
} catch {
  $blockers.Add('remote_readback_exception:' + $_.Exception.Message)
}

$remoteReadbackOk = $null -ne $remoteStatus -and $null -ne $remoteProof -and
  [int]$remoteStatus.verified_csv_rows -eq 300 -and
  [int]$remoteStatus.verified_geojson_features -eq 300 -and
  [int]$remoteStatus.browser_visible_rows -eq 300 -and
  [int]$remoteStatus.new_rows_in_latest_batch -eq 150 -and
  [string]$remoteProof.status -eq 'pass' -and
  [int]$remoteProof.console_error_count -eq 0 -and
  ([string]$remoteProof.latest_filter_rows -match '150\s+sat')
if (-not $remoteReadbackOk) { $blockers.Add('remote_300_site_readback_failed') }

$uniqueBlockers = @($blockers | Select-Object -Unique)
$passed = $uniqueBlockers.Count -eq 0
$result = [ordered]@{
  task_id = $taskId
  recovery_id = 'aays1-169-security-publish-remote-readback-recovery-20260714'
  page_key = 'aays1'
  status = if ($passed) { 'completed_300_security_publish_remote_readback_final_false' } else { 'blocked_300_security_publish_remote_readback' }
  started_at = $startedAt
  completed_at = [DateTimeOffset]::UtcNow.ToString('o')
  verified_csv_rows = [int]$status.verified_csv_rows
  verified_geojson_features = [int]$status.verified_geojson_features
  browser_visible_rows = [int]$status.browser_visible_rows
  new_rows = [int]$status.new_rows_in_latest_batch
  visible_rows_count = $rowCount
  csv_rows_count = $csvCount
  geojson_features = $geoCount
  official_api_lsoa_validated_count = [int]$status.official_api_lsoa_validated_count
  browser_status = [string]$proof.status
  latest_filter_rows = [string]$proof.latest_filter_rows
  console_error_count = [int]$proof.console_error_count
  atomic_publish_commit = '6a036da'
  remote_readback_ok = [bool]$remoteReadbackOk
  completed_gate_count = if ($passed) { 4 } else { 3 }
  total_gate_count = 4
  blockers = $uniqueBlockers
  single_runner_only = $true
  parallel_runner = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json $outputRel $result
Write-Json $statusRel $result
Write-Output ("OUTPUT=" + (Join-Path $repoRoot ($outputRel -replace '/', '\')))
if ($passed) { exit 0 }
exit 2
