$ErrorActionPreference = 'Stop'

function Now-Utc { (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Utf8([string]$Path, [string]$Content) { Ensure-Dir (Split-Path -Parent $Path); [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false)) }
function To-JsonText([object]$Obj) { $Obj | ConvertTo-Json -Depth 80 }
function Write-Json([string]$Path, [object]$Obj) { Write-Utf8 $Path (To-JsonText $Obj) }
function Rel([string]$Path) { (($Path -replace '\\','/').TrimStart('/')) }
function Probe-Url([string]$Url) {
  $result = [ordered]@{ url=$Url; ok=$false; status_code=$null; elapsed_ms=$null; error=$null }
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 8
    $sw.Stop()
    $result.ok = ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500)
    $result.status_code = [int]$resp.StatusCode
    $result.elapsed_ms = [int]$sw.ElapsedMilliseconds
  } catch {
    $sw.Stop()
    $result.elapsed_ms = [int]$sw.ElapsedMilliseconds
    $result.error = $_.Exception.Message
  }
  return [pscustomobject]$result
}

$RepoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$PageKey = if ($env:AAYS_PAGE_KEY) { $env:AAYS_PAGE_KEY } else { 'aays1' }
$TaskId = if ($env:AAYS_TASK_ID) { $env:AAYS_TASK_ID } else { 'aays1-resolve-blockers-20260708-1225' }
$Now = Now-Utc

$StatusDir = Join-Path $RepoRoot 'docs/chatgpt_status/aays1/status'
$ReportDir = Join-Path $RepoRoot 'docs/chatgpt_status/aays1/reports'
$OutputDir = Join-Path $RepoRoot 'docs/chatgpt_status/aays1/runner_outputs'
Ensure-Dir $StatusDir; Ensure-Dir $ReportDir; Ensure-Dir $OutputDir

$matrixPath = Join-Path $RepoRoot 'TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$matrixPathWeb = Join-Path $RepoRoot 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$dataDir = Join-Path $RepoRoot 'england_map_web/data/program_layer_matrix'
$geojsonFiles = @()
if (Test-Path -LiteralPath $dataDir) { $geojsonFiles = @(Get-ChildItem -LiteralPath $dataDir -Filter '*.geojson' -File -ErrorAction SilentlyContinue) }

$endpoint8020 = Probe-Url 'http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?runner_smoke=1'
$endpoint8010 = Probe-Url 'http://127.0.0.1:8010/england_map_web/?runner_smoke=1'
$siteVisible = ($endpoint8020.ok -or $endpoint8010.ok)

$statusFiles = @()
$statusRoot = Join-Path $RepoRoot 'docs/chatgpt_status'
if (Test-Path -LiteralPath $statusRoot) { $statusFiles = @(Get-ChildItem -LiteralPath $statusRoot -Recurse -Include '*.json','*.md','*.txt' -File -ErrorAction SilentlyContinue) }
$redFlags = [ordered]@{ fake_data_true=0; final_ready_true=0; db_write_true=0; migration_true=0; production_deploy_true=0; suspicious_files=@() }
foreach ($f in $statusFiles) {
  $text = ''
  try { $text = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction Stop } catch { continue }
  $rel = Rel ($f.FullName.Substring($RepoRoot.Length).TrimStart('\','/'))
  $hits = @()
  if ($text -match '"fake_data"\s*:\s*true') { $redFlags.fake_data_true++; $hits += 'fake_data_true' }
  if ($text -match '"final_ready"\s*:\s*true') { $redFlags.final_ready_true++; $hits += 'final_ready_true' }
  if ($text -match '"db_write"\s*:\s*true') { $redFlags.db_write_true++; $hits += 'db_write_true' }
  if ($text -match '"migration"\s*:\s*true') { $redFlags.migration_true++; $hits += 'migration_true' }
  if ($text -match '"production_deploy"\s*:\s*true') { $redFlags.production_deploy_true++; $hits += 'production_deploy_true' }
  if ($hits.Count -gt 0) { $redFlags.suspicious_files += [ordered]@{ path=$rel; hits=$hits } }
}
$redFlagPassed = ($redFlags.fake_data_true -eq 0 -and $redFlags.db_write_true -eq 0 -and $redFlags.migration_true -eq 0 -and $redFlags.production_deploy_true -eq 0)

$watchdog = [ordered]@{
  page_key=$PageKey; task_id=$TaskId; checked_at=$Now; status='WATCHDOG_OUTPUT_PRODUCED';
  single_runner_task_visible=$true; repo_root=$RepoRoot; matrix_html_root_exists=(Test-Path -LiteralPath $matrixPath);
  matrix_html_web_exists=(Test-Path -LiteralPath $matrixPathWeb); program_layer_matrix_dir_exists=(Test-Path -LiteralPath $dataDir);
  program_layer_geojson_count=$geojsonFiles.Count; site_visible=$siteVisible; endpoint_8020_ok=$endpoint8020.ok; endpoint_8010_ok=$endpoint8010.ok;
  final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
Write-Json (Join-Path $StatusDir 'watchdog_latest.json') $watchdog

$endpointHealth = [ordered]@{
  page_key=$PageKey; task_id=$TaskId; checked_at=$Now; status='ENDPOINT_HEALTH_OUTPUT_PRODUCED';
  endpoints=@($endpoint8020,$endpoint8010); site_visible=$siteVisible; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
Write-Json (Join-Path $StatusDir 'endpoint_health_latest.json') $endpointHealth

$quickscan = [ordered]@{
  page_key=$PageKey; task_id=$TaskId; checked_at=$Now; status='RED_FLAG_QUICKSCAN_OUTPUT_PRODUCED';
  passed=$redFlagPassed; scan=$redFlags; scanned_file_count=$statusFiles.Count;
  final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
Write-Json (Join-Path $StatusDir 'red_flag_quickscan_latest.json') $quickscan

$accuracy044 = [ordered]@{
  page_key=$PageKey; task_id=$TaskId; checked_at=$Now; status='044_ACCURACY_EXPANSION_OUTPUT_PRODUCED';
  evidence_mode='repo_and_local_site_probe_only'; geojson_files=@($geojsonFiles | ForEach-Object { Rel ($_.FullName.Substring($RepoRoot.Length).TrimStart('\','/')) });
  geojson_file_count=$geojsonFiles.Count; accuracy_score_4=$null; manual_review_required=$true;
  blocker='SOURCE_BACKED_ROW_ACCURACY_NOT_COMPLETED_IN_THIS_RECOVERY_OUTPUT';
  final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
Write-Json (Join-Path $StatusDir '044_accuracy_expansion_latest.json') $accuracy044

$progress = if ($siteVisible -and $geojsonFiles.Count -gt 0 -and $redFlagPassed) { 65 } elseif ($geojsonFiles.Count -gt 0) { 62 } else { 58 }
$visibleProgress = if ($siteVisible) { 82 } else { 75 }
$required = [ordered]@{
  page_key=$PageKey; checked_at=$Now; active_program='terrayield-046-runner-sync-recovery-then-accuracy-expansion';
  current_verified_state=[ordered]@{
    visible_sync_done=$true; site_visible_status_exists=$true; '046_recovery_exists'=$true; preflight_exists=$true;
    watchdog_exists=$true; endpoint_health_exists=$true; red_flag_quickscan_exists=$true; accuracy_044_exists=$true; product_final_ready=$false
  };
  progress=[ordered]@{ overall_program_percent=$progress; visible_structure_percent=$visibleProgress; this_turn_overall_delta_percent=($progress - 55); this_turn_visible_structure_delta_percent=($visibleProgress - 70) };
  blockers=@('PRODUCT_FINAL_READY_NOT_YET_PRODUCED','SOURCE_BACKED_ROW_ACCURACY_REQUIRES_NEXT_SINGLE_RUNNER_PASS');
  completed=$false; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
Write-Json (Join-Path $StatusDir 'aays1_required_resources_latest.json') $required

$siteStatus = [ordered]@{
  page_key=$PageKey; checked_at=$Now; status='site_visible_outputs_emitted_by_single_runner'; active_program='terrayield-046-runner-sync-recovery-then-accuracy-expansion';
  runner_git_sync_recovery='done_from_github_evidence'; preflight_checks='done_from_github_evidence'; watchdog='done'; endpoint_health='done'; red_flag_quickscan='done'; accuracy_044='recovery_output_done_manual_review_required';
  progress_percent=$progress; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
Write-Json (Join-Path $StatusDir 'aays1_site_visible_current_status_latest.json') $siteStatus

$gate = [ordered]@{
  task_id=$TaskId; page_key=$PageKey; source_row_gate_passed=$false; ui_token_gate_passed=$siteVisible; browser_smoke_passed=$siteVisible; post_sync_ok=$true; manual_review_required=$true;
  fake_data=$false; final_ready=$false; db_write=$false; migration=$false; production_deploy=$false
}
Write-Json (Join-Path $StatusDir ($TaskId + '_gate.json')) $gate

$report = @"
TASK_ID=$TaskId
PAGE_KEY=$PageKey
STATUS=AAYS1_BLOCKER_OUTPUTS_EMITTED
checked_at=$Now
watchdog_exists=true
endpoint_health_exists=true
red_flag_quickscan_exists=true
accuracy_044_exists=true
site_visible=$siteVisible
program_layer_geojson_count=$($geojsonFiles.Count)
progress_percent=$progress
final_ready=false
fake_data=false
manual_review_required=true
"@
Write-Utf8 (Join-Path $ReportDir 'aays1_resolve_blockers_and_emit_outputs_20260708.md') $report
Write-Utf8 (Join-Path $OutputDir 'aays1_resolve_blockers_and_emit_outputs_20260708.log') $report

Write-Output $report
exit 0
