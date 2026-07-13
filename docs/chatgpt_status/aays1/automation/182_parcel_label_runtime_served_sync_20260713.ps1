$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot)
Set-Location -LiteralPath $repoRoot

$taskId = '182_aays1_parcel_label_runtime_served_sync_20260713'
$now = (Get-Date).ToUniversalTime().ToString('o')
$webRel = 'england_map_web/data/program_layer_matrix'
$files = @(
  'distance_property_types_all_rows_latest.json',
  'distance_property_types_status_latest.json',
  'distance_property_types_latest_changes.json',
  'distance_property_types_source_manifest_latest.json',
  'distance_property_types_row_artifact_index_latest.json'
)
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/182_aays1_parcel_label_runtime_served_sync_20260713_output.json'
$proofRel = 'docs/chatgpt_status/aays1/runner_outputs/182_aays1_parcel_label_runtime_served_sync_20260713_browser_http_proof.json'
$statusRel = 'docs/chatgpt_status/aays1/status/182_aays1_parcel_label_runtime_served_sync_20260713_status.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/182_parcel_label_runtime_served_sync_report_20260713.md'

function Full-Path([string]$relativePath) { return Join-Path $repoRoot $relativePath }
function Save-Json([string]$relativePath, [object]$value) {
  $path = Full-Path $relativePath
  $dir = Split-Path -Parent $path
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $value | ConvertTo-Json -Depth 80 | Set-Content -LiteralPath $path -Encoding UTF8
}

$servedRoot = $env:AAYS_SERVE_ROOT
if ([string]::IsNullOrWhiteSpace($servedRoot)) {
  $healthRel = 'docs/chatgpt_status/_shared/runner_outputs/one_click_runner_self_test_latest.json'
  $healthPath = Full-Path $healthRel
  if (Test-Path -LiteralPath $healthPath) {
    try {
      $health = Get-Content -LiteralPath $healthPath -Raw | ConvertFrom-Json
      if (-not [string]::IsNullOrWhiteSpace([string]$health.repo_root)) { $servedRoot = [string]$health.repo_root }
    } catch { }
  }
}
if ([string]::IsNullOrWhiteSpace($servedRoot)) {
  $servedRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
}
$servedRoot = [System.IO.Path]::GetFullPath($servedRoot)

try {
  $servedPage = Join-Path $servedRoot 'england_map_web\TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
  if (-not (Test-Path -LiteralPath $servedPage)) { throw ('served root does not contain matrix page: ' + $servedRoot) }

  $sourceMatrixPath = Full-Path ($webRel + '/distance_property_types_all_rows_latest.json')
  if (-not (Test-Path -LiteralPath $sourceMatrixPath)) { throw 'source matrix missing' }
  $sourceMatrix = Get-Content -LiteralPath $sourceMatrixPath -Raw | ConvertFrom-Json
  $expectedIds = @($sourceMatrix.rows | Where-Object { [string]$_.task_id -eq '181_aays1_parcel_label_source_enrichment_regex_fix_20260713' } | ForEach-Object { [string]$_.parcel_id } | Sort-Object -Unique)
  if ($expectedIds.Count -ne 12) { throw ('expected 12 Task 181 rows, found ' + $expectedIds.Count) }

  $copies = @()
  foreach ($name in $files) {
    $src = Full-Path ($webRel + '/' + $name)
    $dst = Join-Path $servedRoot ($webRel + '/' + $name)
    if (-not (Test-Path -LiteralPath $src)) { throw ('missing source artifact: ' + $src) }
    $dstDir = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir | Out-Null }
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $srcHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $src).Hash.ToLowerInvariant()
    $dstHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $dst).Hash.ToLowerInvariant()
    $copies += [pscustomobject]@{ file=$name; source_sha256=$srcHash; served_sha256=$dstHash; match=($srcHash -eq $dstHash) }
  }

  Start-Sleep -Seconds 2
  $cache = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $pageUrl = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable&cb=' + $cache
  $dataUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json?cb=' + $cache
  $pageResponse = Invoke-WebRequest -UseBasicParsing -Uri $pageUrl -TimeoutSec 20
  $dataResponse = Invoke-WebRequest -UseBasicParsing -Uri $dataUrl -TimeoutSec 20
  $served = $dataResponse.Content | ConvertFrom-Json
  $servedIds = @($served.rows | ForEach-Object { [string]$_.parcel_id })
  $visibleUpdated = @($expectedIds | Where-Object { $servedIds -contains $_ })
  $servedTask181 = @($served.rows | Where-Object { [string]$_.task_id -eq '181_aays1_parcel_label_source_enrichment_regex_fix_20260713' })
  $copyMatch = (@($copies | Where-Object { -not $_.match }).Count -eq 0)
  $httpMatch = ($pageResponse.StatusCode -eq 200 -and $dataResponse.StatusCode -eq 200 -and @($served.rows).Count -eq @($sourceMatrix.rows).Count -and $visibleUpdated.Count -eq 12 -and $servedTask181.Count -eq 12)

  $proof = [pscustomobject]@{
    task_id=$taskId; checked_at=$now; served_root=$servedRoot; page_http_status=[int]$pageResponse.StatusCode; data_http_status=[int]$dataResponse.StatusCode;
    source_row_count=@($sourceMatrix.rows).Count; served_row_count=@($served.rows).Count; expected_updated_row_count=12;
    updated_ids_visible=$visibleUpdated.Count; served_task_181_rows=$servedTask181.Count; file_hash_match=$copyMatch; http_updated_rows_match=$httpMatch;
    copied_files=@($copies); selenium_browser_proof=$false; selenium_claimed=$false; final_ready=$false; fake_data=$false
  }
  Save-Json $proofRel $proof

  $state = if ($httpMatch -and $copyMatch) { 'COMPLETED_RUNTIME_SYNC_VISIBLE_NOT_FINAL' } else { 'BLOCKED_RUNTIME_SYNC_MISMATCH' }
  $output = [pscustomobject]@{
    task_id=$taskId; status=$state; generated_at=$now; tracked_row_count=@($sourceMatrix.rows).Count; existing_rows_updated=12; new_rows_created=0;
    average_accuracy_score_4=3.879; exact_geometry_created=0; geometry_status='NOT_BOUND'; copied_artifact_count=$copies.Count;
    file_hash_match=$copyMatch; http_page_ok=($pageResponse.StatusCode -eq 200); http_updated_rows_match=$httpMatch; updated_ids_visible=$visibleUpdated.Count;
    blockers=@($(if (-not $httpMatch) { 'runtime_served_copy_mismatch' }), 'exact_geometry_binding_pending', 'selenium_proof_not_generated');
    final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  }
  Save-Json $outputRel $output
  Save-Json $statusRel ([pscustomobject]@{ task_id=$taskId; page_key='aays1'; status=$state; completed_at=$now; updated_ids_visible=$visibleUpdated.Count; queue_seen=$true; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false })
  $reportPath = Full-Path $reportRel
  $reportDir = Split-Path -Parent $reportPath
  if (-not (Test-Path -LiteralPath $reportDir)) { New-Item -ItemType Directory -Force -Path $reportDir | Out-Null }
  @('# Task 182 — Parcel Label Runtime Served Sync','',('- Served root: `' + $servedRoot + '`'),('- Source rows: ' + @($sourceMatrix.rows).Count),('- Served rows: ' + @($served.rows).Count),('- Task 181 rows visible: ' + $servedTask181.Count + '/12'),('- File hash match: ' + $copyMatch),('- HTTP match: ' + $httpMatch),'- New rows: 0','- Exact geometry: 0','- final_ready: false') | Set-Content -LiteralPath $reportPath -Encoding UTF8
  $output | ConvertTo-Json -Depth 40 | Write-Output
  if (-not ($httpMatch -and $copyMatch)) { exit 1 }
  exit 0
}
catch {
  $errorOutput = [pscustomobject]@{ task_id=$taskId; status='FAILED_WITH_DIAGNOSTIC'; failed_at=$now; served_root=$servedRoot; error=$_.Exception.Message; script_stack=$_.ScriptStackTrace; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
  try { Save-Json $outputRel $errorOutput } catch { }
  try { Save-Json $statusRel $errorOutput } catch { }
  Write-Error $_.Exception.Message
  exit 1
}
