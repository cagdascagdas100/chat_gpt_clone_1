param(
  [string]$RepoRoot = $(if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { 'F:\chatgpt\chat_gpt_clone_1_main' }),
  [string]$TaskId = $(if ($env:AAYS_TASK_ID) { $env:AAYS_TASK_ID } else { 'security_public_safety_batch_20260703_0001' })
)

$ErrorActionPreference = 'Stop'
$PageKey = 'security_public_safety'
$Layer = 'Safety / Security'
$ProgramOutput = 'Security Level percent'
$Now = (Get-Date).ToString('o')

$ReportDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\reports"
$StatusDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
$DataDir = Join-Path $RepoRoot 'england_map_web\data\security_public_safety'
$WebUpdateDir = Join-Path $RepoRoot 'outputs\england_program_parcel_matrix_20260629\security_public_safety_updates'
New-Item -ItemType Directory -Force -Path $ReportDir, $StatusDir, $DataDir, $WebUpdateDir | Out-Null

$GeoJsonPath = Join-Path $DataDir 'parcel_security_scores_verified.geojson'
$CsvPath = Join-Path $DataDir 'parcel_security_scores_verified.csv'
$ManifestPath = Join-Path $DataDir 'security_evidence_manifest.json'
$LatestChangesPath = Join-Path $WebUpdateDir 'latest_changes.json'
$ReportPath = Join-Path $ReportDir "$TaskId.md"
$StatusPath = Join-Path $StatusDir "$TaskId.status.json"

$blockers = New-Object System.Collections.Generic.List[string]
if (-not (Test-Path -LiteralPath $GeoJsonPath)) { $blockers.Add('Missing parcel_security_scores_verified.geojson with verified parcel features.') }
if (-not (Test-Path -LiteralPath $CsvPath)) { $blockers.Add('Missing parcel_security_scores_verified.csv with official/open aggregate source evidence.') }
if (-not (Test-Path -LiteralPath $ManifestPath)) { $blockers.Add('Missing security_evidence_manifest.json.') }
if ($blockers.Count -eq 0) { $blockers.Add('Bootstrap runner does not yet validate source/schema/site/browser smoke evidence. final_ready remains false.') }

$latest = [ordered]@{
  layer = $Layer
  program_output = $ProgramOutput
  status = 'BLOCKED_WAITING_FOR_REAL_RUNNER_OUTPUT'
  fake_data = $false
  db_write = $false
  migration_apply = $false
  prod_deploy = $false
  last_updated = $Now
  summary = [ordered]@{
    changed_count = 0
    verified_count = 0
    manual_review_count = 0
    accuracy_ge_3_count = 0
    final_ready = $false
  }
  changes = @()
  blockers = $blockers.ToArray()
  next_single_action = 'Run a real read-only parcel batch using official/open aggregate public-safety evidence; then update verified CSV/GeoJSON/manifest and browser smoke proof.'
}
$latest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $LatestChangesPath -Encoding UTF8

@"
# Security Public Safety Batch Report

page_key=$PageKey
task_id=$TaskId
layer=$Layer
program_output=$ProgramOutput
run_finished_at=$Now
status=BLOCKED_WAITING_FOR_VERIFIED_INPUTS
input_rows=0
processed_rows=0
verified_rows=0
manual_review_rows=0
accuracy_ge_3_rows=0
accuracy_lt_3_rows=0
no_data_rows=0
geojson_output=$GeoJsonPath
csv_output=$CsvPath
manifest_output=$ManifestPath
site_updates_output=$LatestChangesPath
fake_data=false
db_write=false
ddl=false
migration_apply=false
prod_deploy=false
final_ready=false

## Blockers

$($blockers | ForEach-Object { "- $_" } | Out-String)

## Next single action

Run a real read-only parcel batch using official/open aggregate public-safety evidence, then validate parcel layer, popup/right-panel fields, latest_changes.json panel rendering, and browser smoke evidence before changing final_ready.
"@ | Set-Content -LiteralPath $ReportPath -Encoding UTF8

@{
  page_key = $PageKey
  task_id = $TaskId
  status = 'BLOCKED_WAITING_FOR_VERIFIED_INPUTS'
  final_ready = $false
  fake_data = $false
  report_path = $ReportPath
  latest_changes_path = $LatestChangesPath
  generated_at = $Now
  blockers = $blockers.ToArray()
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $StatusPath -Encoding UTF8

Write-Output "REPORT=$ReportPath"
Write-Output "STATUS=$StatusPath"
Write-Output "SITE_UPDATES=$LatestChangesPath"
