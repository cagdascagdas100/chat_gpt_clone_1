[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }
function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}
function Write-Json([string]$Path, [object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText($Path, (($Value | ConvertTo-Json -Depth 70) + "`n"), [System.Text.UTF8Encoding]::new($false))
}
function Read-Json([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function Set-Prop([object]$Object, [string]$Name, [object]$Value) {
  Add-Member -InputObject $Object -NotePropertyName $Name -NotePropertyValue $Value -Force
}
function Get-Prop([object]$Object, [string]$Name) {
  if ($null -eq $Object) { return $null }
  $p = $Object.PSObject.Properties[$Name]
  if ($p) { return $p.Value }
  return $null
}
function Get-Python {
  foreach ($candidate in @('python','py')) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
  }
  return $null
}
function Get-Median([double[]]$Values) {
  $sorted = @($Values | Sort-Object)
  if ($sorted.Count -eq 0) { return $null }
  $mid = [int][math]::Floor($sorted.Count / 2)
  if (($sorted.Count % 2) -eq 1) { return [double]$sorted[$mid] }
  return ([double]$sorted[$mid - 1] + [double]$sorted[$mid]) / 2.0
}
function Invoke-ElevationDataset([string]$Dataset, [object[]]$Rows) {
  $locations = ($Rows | ForEach-Object { ('{0},{1}' -f $_.centroid_lat, $_.centroid_lon) }) -join '|'
  $requestEndpoint = "https://api.opentopodata.org/v1/$Dataset"
  $requestUrl = "$requestEndpoint?locations=$([System.Uri]::EscapeDataString($locations))&interpolation=bilinear"
  $payload = [ordered]@{
    dataset = $Dataset
    request_method = 'POST'
    request_url = $requestUrl
    request_locations = $locations
    reachable = $false
    api_status = 'NOT_RUN'
    result_count = 0
    elevations = @()
    response = $null
    error = $null
  }
  try {
    $response = Invoke-RestMethod -Method Post -Uri $requestEndpoint -Body @{locations=$locations;interpolation='bilinear'} -ContentType 'application/x-www-form-urlencoded' -TimeoutSec 120 -Headers @{ 'User-Agent'='TerraYield-AAYS-Topography/1.0 extended-consensus' }
    $results = @($response.results)
    if ([string]$response.status -ne 'OK') { throw "${Dataset}_API_STATUS_$($response.status)" }
    if ($results.Count -ne $Rows.Count) { throw "${Dataset}_RESULT_COUNT_$($results.Count)_EXPECTED_$($Rows.Count)" }
    foreach ($result in $results) {
      if ($null -eq $result.elevation -or [double]::IsNaN([double]$result.elevation)) { throw "${Dataset}_NULL_OR_NAN_ELEVATION" }
    }
    $payload.reachable = $true
    $payload.api_status = 'OK'
    $payload.result_count = $results.Count
    $payload.elevations = @($results | ForEach-Object { [math]::Round([double]$_.elevation, 2) })
    $payload.response = $response
  } catch {
    $payload.api_status = 'BLOCKED_OR_UNAVAILABLE'
    $payload.error = $_.Exception.Message
  }
  return [pscustomobject]$payload
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or $repoRoot -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]') {
  throw 'TOPOGRAPHY_159_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'aays1-159-topography-official-source-acceleration-bridge-20260711' }
$branch = if ($env:AAYS_TARGET_BRANCH) { [string]$env:AAYS_TARGET_BRANCH } else { 'codex/aays-single-runner-v5-20260706' }
$startedAt = Now-Utc
$stages = @()

$script158Rel = 'docs/chatgpt_status/topography/automation/158_topography_official_source_acceleration_batch_20260711.ps1'
$output158Rel = 'docs/chatgpt_status/topography/runner_outputs/158_topography_official_source_acceleration_batch.json'
$visibleRowsRel = 'england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$visibleStatusRel = 'england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$htmlRel = 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$latestChangesRel = 'outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'
$sourceSnapshotRel = 'docs/chatgpt_status/topography/source_snapshots/159_extended_consensus_sources_latest.json'
$consensusRowsRel = 'docs/chatgpt_status/topography/fixtures/topography_extended_consensus_rows_20260711.json'
$consensusCsvRel = 'docs/chatgpt_status/topography/fixtures/topography_extended_consensus_rows_20260711.csv'
$statusRel = 'docs/chatgpt_status/topography/status/159_topography_extended_consensus_latest.json'
$reportRel = 'docs/chatgpt_status/topography/reports/159_topography_extended_consensus_report_20260711.md'
$browserProofRel = 'docs/chatgpt_status/topography/reports/159_topography_extended_consensus_browser_validation_20260711.json'
$runnerOutputRel = 'docs/chatgpt_status/topography/runner_outputs/159_topography_extended_consensus_batch.json'
$operationsRel = 'england_map_web/data/program_layer_matrix/topography_operations_latest.json'
$operationsStatusRel = 'docs/chatgpt_status/topography/status/topography_operations_latest.json'
function Write-OperationLedger([object[]]$StageItems,[object[]]$ParcelRows,[string]$RunStatus,[string]$FailureBlocker='') {
  $now=Now-Utc; $runKey=($startedAt -replace '[^0-9]',''); $ops=@(); $sequence=0
  foreach($stageItem in @($StageItems)){
    $sequence++; $stageName=[string](Get-Prop $stageItem 'stage'); $stageStatus=[string](Get-Prop $stageItem 'status')
    $blocked=($stageStatus -match 'blocked|unavailable|failed'); $ops += [ordered]@{
      operation_id="${taskId}_${runKey}_stage_$sequence"; task_id=$taskId; page_key='topography'; operation_type='pipeline_stage'; stage_index=$sequence; stage=$stageName; dataset=$stageName; source_url=if($stageName -match 'srtm30'){$srtm30.request_url}elseif($stageName -match 'aster30'){$aster30.request_url}else{$null}; request_status=$stageStatus; numeric_sample_status=if($stageName -match 'source|catalogue|discovery'){'SOURCE_REACHABILITY_ONLY'}else{$stageStatus}; parcel_id=$null; started_at=$startedAt; completed_at=$now; status=if($blocked){'blocked'}else{$stageStatus}; source_path=$sourceSnapshotRel; evidence_path=$sourceSnapshotRel; report_path=$reportRel; runner_output_path=$runnerOutputRel; blocker=if($blocked){$stageStatus}else{''}; is_new_operation=$true; final_ready=$false; fake_data=$false
    }
  }
  foreach($parcel in @($ParcelRows)){
    $sequence++; $ops += [ordered]@{operation_id="${taskId}_${runKey}_parcel_$([string]$parcel.parcel_id)";task_id=$taskId;page_key='topography';operation_type='parcel_result';stage_index=$sequence;stage='parcel_consensus_result';dataset=[string]$parcel.consensus_sources;source_url=[string]$parcel.source_url;request_status='completed';numeric_sample_status='REAL_NUMERIC_VALUES_FROM_RECORDED_DEM_RESPONSES';parcel_id=[string]$parcel.parcel_id;parcel_ref=[string]$parcel.parcel_ref;centroid_lat=$parcel.centroid_lat;centroid_lon=$parcel.centroid_lon;elevation_consensus_median_m=$parcel.elevation_consensus_median_m;source_spread_m=$parcel.source_spread_m;started_at=$startedAt;completed_at=$now;status=[string]$parcel.consensus_status;source_path=$consensusRowsRel;evidence_path=$consensusRowsRel;report_path=$reportRel;runner_output_path=$runnerOutputRel;blocker=[string]$parcel.blocker;is_new_operation=$true;final_ready=$false;fake_data=$false}
  }
  if($FailureBlocker){$sequence++;$ops += [ordered]@{operation_id="${taskId}_${runKey}_failure_$sequence";task_id=$taskId;page_key='topography';operation_type='runner_failure';stage_index=$sequence;stage='task_159';dataset=$null;source_url=$null;request_status='failed';numeric_sample_status='NOT_PRODUCED';parcel_id=$null;started_at=$startedAt;completed_at=$now;status='blocked';source_path=$null;evidence_path=$statusRel;report_path=$reportRel;runner_output_path=$runnerOutputRel;blocker=$FailureBlocker;is_new_operation=$true;final_ready=$false;fake_data=$false}}
  $path=Join-Path $repoRoot ($operationsRel-replace'/','\');$old=Read-Json $path;$existing=@(if($old){$old.operations}else{@()});$seen=@{};foreach($op in $existing){$seen[[string]$op.operation_id]=$true};foreach($op in $ops){if(-not$seen.ContainsKey([string]$op.operation_id)){$existing+=$op}}
  $blockedOps=@($existing|Where-Object{$_.status-match'blocked|failed|unavailable|request_failed|not_downloaded'})
  $payload=[ordered]@{task_id=$taskId;updated_at=$now;run_status=$RunStatus;operation_count=$existing.Count;new_operations_count=$ops.Count;blocked_operation_count=$blockedOps.Count;last_blocked_operation=if($blockedOps.Count){$blockedOps[-1]}else{$null};operations=$existing;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
  Write-Json $path $payload; Write-Json (Join-Path $repoRoot ($operationsStatusRel-replace'/','\')) $payload
}

try {
  # Stages 1-9: execute or reuse the complete task-158 chain in this same canonical runner process.
  $output158Path = Join-Path $repoRoot ($output158Rel -replace '/', '\')
  $output158 = Read-Json $output158Path
  if ($null -eq $output158 -or [string]$output158.status -ne 'COMPLETED_VISIBLE_NOT_FINAL') {
    $script158Path = Join-Path $repoRoot ($script158Rel -replace '/', '\')
    if (-not (Test-Path -LiteralPath $script158Path)) { throw 'TASK_158_SCRIPT_MISSING' }
    $savedTaskId = $env:AAYS_TASK_ID
    $task158Error = $null
    try {
      $env:AAYS_TASK_ID = 'topography-158-official-source-acceleration-batch-20260711'
      & powershell -NoProfile -ExecutionPolicy Bypass -File $script158Path
      if ($LASTEXITCODE -ne 0) { $task158Error = "TASK_158_EXIT_CODE_$LASTEXITCODE" }
    } catch {
      $task158Error = $_.Exception.Message
    } finally {
      $env:AAYS_TASK_ID = $savedTaskId
    }
    $output158 = Read-Json $output158Path
    if ($null -ne $output158 -and [string]$output158.status -eq 'COMPLETED_VISIBLE_NOT_FINAL') {
      $stages += [ordered]@{ stage='official_source_acceleration_chain'; status='completed_in_same_runner_process'; inherited_stage_count=9 }
    } else {
      $stages += [ordered]@{ stage='official_source_acceleration_chain'; status='blocked_source_api_continuing_with_existing_real_dem_rows'; inherited_stage_count=9; blocker=if($task158Error){$task158Error}else{'TASK_158_OUTPUT_NOT_READY_AFTER_RUN'} }
    }
  } else {
    $stages += [ordered]@{ stage='official_source_acceleration_chain'; status='reused_existing_runner_output'; inherited_stage_count=9 }
  }

  $visibleRowsPath = Join-Path $repoRoot ($visibleRowsRel -replace '/', '\')
  $visible = Read-Json $visibleRowsPath
  $rows = @($visible.rows)
  if ($null -eq $visible -or $rows.Count -lt 3) { throw 'VISIBLE_ROWS_NOT_READY_FOR_159' }

  # Stage 10: higher-resolution SRTM 30 m quality-control sample.
  $srtm30 = Invoke-ElevationDataset 'srtm30m' $rows
  $stages += [ordered]@{ stage='srtm30m_quality_control'; status=if($srtm30.reachable){'completed'}else{'blocked_or_unavailable'}; rows=$srtm30.result_count }

  # Stage 11: independent ASTER 30 m quality-control sample.
  $aster30 = Invoke-ElevationDataset 'aster30m' $rows
  $stages += [ordered]@{ stage='aster30m_quality_control'; status=if($aster30.reachable){'completed'}else{'blocked_or_unavailable'}; rows=$aster30.result_count }

  $generatedAt = Now-Utc
  Write-Json (Join-Path $repoRoot ($sourceSnapshotRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId
    generated_at=$generatedAt
    srtm30m=$srtm30
    aster30m=$aster30
    final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  })

  # Stage 12: calculate a reproducible multi-DEM median, source spread and outlier status.
  $consensusRows = @()
  for ($i=0; $i -lt $rows.Count; $i++) {
    $row = $rows[$i]
    $named = [ordered]@{}
    $eudem = Get-Prop $row 'elevation_sea_level_m'
    $srtm90 = Get-Prop $row 'secondary_elevation_m'
    if ($null -ne $eudem) { $named['EUDEM25M'] = [math]::Round([double]$eudem,2) }
    if ($null -ne $srtm90) { $named['SRTM90M'] = [math]::Round([double]$srtm90,2) }
    if ($srtm30.reachable) { $named['SRTM30M'] = [double]$srtm30.elevations[$i] }
    if ($aster30.reachable) { $named['ASTER30M'] = [double]$aster30.elevations[$i] }
    $values = @($named.Values | ForEach-Object { [double]$_ })
    if ($values.Count -lt 2) { throw "CONSENSUS_REQUIRES_AT_LEAST_TWO_SOURCES_$($row.parcel_id)" }
    $median = [math]::Round([double](Get-Median $values),2)
    $minimum = [math]::Round([double](($values | Measure-Object -Minimum).Minimum),2)
    $maximum = [math]::Round([double](($values | Measure-Object -Maximum).Maximum),2)
    $spread = [math]::Round($maximum - $minimum,2)
    $consensusStatus = if ($spread -le 3) { 'HIGH_CONSISTENCY_WITHIN_3M' } elseif ($spread -le 8) { 'MODERATE_CONSISTENCY_WITHIN_8M' } elseif ($spread -le 15) { 'WIDE_SPREAD_MANUAL_REVIEW' } else { 'HIGH_DIVERGENCE_MANUAL_REVIEW' }
    $consensusRows += [pscustomobject][ordered]@{
      parcel_id=$row.parcel_id
      parcel_ref=$row.parcel_ref
      centroid_lat=$row.centroid_lat
      centroid_lon=$row.centroid_lon
      eudem25m_elevation_m=$eudem
      srtm90m_elevation_m=$srtm90
      srtm30m_elevation_m=if($srtm30.reachable){[double]$srtm30.elevations[$i]}else{$null}
      aster30m_elevation_m=if($aster30.reachable){[double]$aster30.elevations[$i]}else{$null}
      consensus_source_count=$values.Count
      elevation_consensus_median_m=$median
      source_min_m=$minimum
      source_max_m=$maximum
      source_spread_m=$spread
      consensus_status=$consensusStatus
      consensus_sources=($named.Keys -join ',')
      accuracy_score_4='2.5/4 fallback multi-DEM consensus; primary CopDEM raster, real parcel boundary and official LiDAR/OS Terrain numeric validation pending'
      needs_manual_review=$true
      changed_in_latest_run=$true
      final_ready=$false
      fake_data=$false
    }
  }
  Write-Json (Join-Path $repoRoot ($consensusRowsRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId
    generated_at=$generatedAt
    row_count=$consensusRows.Count
    rows=$consensusRows
    final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  })
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($consensusCsvRel -replace '/', '\')))
  $consensusRows | Export-Csv -LiteralPath (Join-Path $repoRoot ($consensusCsvRel -replace '/', '\')) -NoTypeInformation -Encoding UTF8
  $stages += [ordered]@{ stage='multi_dem_consensus_calculation'; status='completed'; rows=$consensusRows.Count }

  # Stage 13: publish all new QC values and evidence paths row by row.
  foreach ($row in $rows) {
    $consensus = $consensusRows | Where-Object { $_.parcel_id -eq $row.parcel_id } | Select-Object -First 1
    Set-Prop $row 'srtm30m_elevation_m' $consensus.srtm30m_elevation_m
    Set-Prop $row 'aster30m_elevation_m' $consensus.aster30m_elevation_m
    Set-Prop $row 'consensus_source_count' $consensus.consensus_source_count
    Set-Prop $row 'elevation_consensus_median_m' $consensus.elevation_consensus_median_m
    Set-Prop $row 'source_spread_m' $consensus.source_spread_m
    Set-Prop $row 'consensus_status' $consensus.consensus_status
    Set-Prop $row 'consensus_sources' $consensus.consensus_sources
    Set-Prop $row 'extended_consensus_evidence_path' $consensusRowsRel
    Set-Prop $row 'extended_source_snapshot_path' $sourceSnapshotRel
    Set-Prop $row 'display_badge' 'EXTENDED_MULTI_DEM_CONSENSUS_READY'
    Set-Prop $row 'sampling_status' 'eudem_srtm90_srtm30_aster_quality_control_completed_or_recorded'
    Set-Prop $row 'accuracy_score_4' $consensus.accuracy_score_4
    Set-Prop $row 'task_id' $taskId
    Set-Prop $row 'updated_at' $generatedAt
    Set-Prop $row 'report_path' $reportRel
    Set-Prop $row 'status_path' $statusRel
    Set-Prop $row 'queue_path' 'docs/chatgpt_status/aays1/queue/aays1_159_topography_official_source_acceleration_bridge_20260711.task.json'
    Set-Prop $row 'blocker' 'real_parcel_boundary_required; primary_copdem_glo30_raster_sampling_required; ea_lidar_or_os_terrain_numeric_validation_required'
    Set-Prop $row 'needs_manual_review' $true
    Set-Prop $row 'final_ready' $false
    Set-Prop $row 'fake_data' $false
  }
  Set-Prop $visible 'status' 'EXTENDED_MULTI_DEM_CONSENSUS_VISIBLE_PRIMARY_VALIDATION_PENDING'
  Set-Prop $visible 'latest_task_id' $taskId
  Set-Prop $visible 'updated_at' $generatedAt
  Set-Prop $visible 'rows' $rows
  Set-Prop $visible 'final_ready' $false
  Set-Prop $visible 'fake_data' $false
  Write-Json $visibleRowsPath $visible

  $visibleStatusPath = Join-Path $repoRoot ($visibleStatusRel -replace '/', '\')
  $visibleStatus = Read-Json $visibleStatusPath
  if ($null -eq $visibleStatus) { $visibleStatus = [pscustomobject]@{} }
  Set-Prop $visibleStatus 'status' 'EXTENDED_MULTI_DEM_CONSENSUS_VISIBLE_PRIMARY_VALIDATION_PENDING'
  Set-Prop $visibleStatus 'latest_task_id' $taskId
  Set-Prop $visibleStatus 'visible_rows_count' $rows.Count
  Set-Prop $visibleStatus 'srtm30m_rows' ([int]$srtm30.result_count)
  Set-Prop $visibleStatus 'aster30m_rows' ([int]$aster30.result_count)
  Set-Prop $visibleStatus 'consensus_rows' $consensusRows.Count
  Set-Prop $visibleStatus 'consensus_evidence_path' $consensusRowsRel
  Set-Prop $visibleStatus 'source_snapshot_path' $sourceSnapshotRel
  $extraDatasetCount = @($srtm30,$aster30 | Where-Object { $_.reachable }).Count
  $completionPercent = if ($extraDatasetCount -eq 2) { 60 } elseif ($extraDatasetCount -eq 1) { 58 } else { 55 }
  Set-Prop $visibleStatus 'completion_percent' $completionPercent
  Set-Prop $visibleStatus 'updated_at' $generatedAt
  Set-Prop $visibleStatus 'final_ready' $false
  Set-Prop $visibleStatus 'fake_data' $false
  Write-Json $visibleStatusPath $visibleStatus

  $htmlPath = Join-Path $repoRoot ($htmlRel -replace '/', '\')
  $html = Get-Content -LiteralPath $htmlPath -Raw -Encoding UTF8
  if (-not $html.Contains("['Consensus median','elevation_consensus_median_m']")) {
    $needle = "['Resmi kaynak discovery','official_source_discovery_path'],['Güven (%)','confidence_percent']"
    $replacement = "['Resmi kaynak discovery','official_source_discovery_path'],['SRTM 30 m','srtm30m_elevation_m'],['ASTER 30 m','aster30m_elevation_m'],['Consensus kaynak sayısı','consensus_source_count'],['Consensus median','elevation_consensus_median_m'],['Kaynak yayılımı (m)','source_spread_m'],['Consensus durumu','consensus_status'],['Consensus kaynakları','consensus_sources'],['Consensus kanıtı','extended_consensus_evidence_path'],['Güven (%)','confidence_percent']"
    if (-not $html.Contains($needle)) { throw 'TOPOGRAPHY_159_HTML_INSERT_POINT_NOT_FOUND' }
    $html = $html.Replace($needle, $replacement)
    [System.IO.File]::WriteAllText($htmlPath, $html, [System.Text.UTF8Encoding]::new($false))
  }
  $stages += [ordered]@{ stage='extended_consensus_site_rows'; status='completed'; rows=$rows.Count }
  Write-OperationLedger -StageItems $stages -ParcelRows $rows -RunStatus 'RUNNING_BROWSER_GATE'
  if($env:AAYS_CONTROLLER_REPO_ROOT){$publisher=Join-Path $repoRoot 'docs/chatgpt_status/_shared/automation/PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1';$publishArg=(@($visibleRowsRel,$visibleStatusRel,$operationsRel,$htmlRel)-join'|');& powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $repoRoot -ControllerRoot $env:AAYS_CONTROLLER_REPO_ROOT -Paths $publishArg -AllowGeneratedArtifacts -SyncPortableWeb;if($LASTEXITCODE-ne0){throw'TOPOGRAPHY_LIVE_CONTROLLER_PUBLISH_BLOCKED'}}

  # Stage 14: third real Chrome/Selenium validation after the extended consensus columns are published.
  $python = Get-Python
  if (-not $python) { throw 'PYTHON_NOT_FOUND_FOR_159_BROWSER_VALIDATION' }
  $portableCursor = $repoRoot
  while ($portableCursor -and (Split-Path -Leaf $portableCursor) -ne 'runner_system') {
    $portableParent = Split-Path -Parent $portableCursor
    if ($portableParent -eq $portableCursor) { break }
    $portableCursor = $portableParent
  }
  if ((Split-Path -Leaf $portableCursor) -ne 'runner_system') { throw 'F_PORTABLE_ROOT_NOT_RESOLVED_FOR_TOPOGRAPHY_BROWSER_TEMP' }
  $portableTempRoot = Join-Path (Split-Path -Parent $portableCursor) '_portable_logs\temp'
  Ensure-Dir $portableTempRoot
  $tempPy = Join-Path $portableTempRoot ("aays_topography_159_" + [guid]::NewGuid().ToString('N') + '.py')
  $tempJson = Join-Path $portableTempRoot ("aays_topography_159_" + [guid]::NewGuid().ToString('N') + '.json')
  $pyCode = @'
import json, sys, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
out_path = sys.argv[1]
url = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?topography_browser_validation=159'
options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=2600,1300')
options.set_capability('goog:loggingPrefs', {'browser':'ALL'})
driver = webdriver.Chrome(options=options)
result = {'status':'FAIL','url':url,'browser':'Google Chrome via Selenium'}
try:
    driver.get(url)
    WebDriverWait(driver,20).until(EC.presence_of_element_located((By.ID,'layerSelect')))
    Select(driver.find_element(By.ID,'layerSelect')).select_by_value('topography')
    driver.execute_script("document.getElementById('layerSelect').dispatchEvent(new Event('change'))")
    WebDriverWait(driver,30).until(lambda d: len(d.find_elements(By.CSS_SELECTOR,'#table tbody tr')) >= 3)
    time.sleep(2)
    text = driver.find_element(By.TAG_NAME,'body').text
    severe = [x for x in driver.get_log('browser') if str(x.get('level','')).upper() == 'SEVERE']
    result.update({
      'status':'PASS',
      'rendered_rows':len(driver.find_elements(By.CSS_SELECTOR,'#table tbody tr')),
      'extended_badge_visible':'EXTENDED_MULTI_DEM_CONSENSUS_READY' in text,
      'srtm30_column_visible':'SRTM 30 m' in text,
      'aster30_column_visible':'ASTER 30 m' in text,
      'consensus_median_visible':'Consensus median' in text,
      'source_spread_visible':'Kaynak yayılımı (m)' in text,
      'consensus_status_visible':'Consensus durumu' in text,
      'console_errors':severe,
      'page_text_sample':text[:5000]
    })
finally:
    driver.quit()
with open(out_path,'w',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
'@
  [System.IO.File]::WriteAllText($tempPy, $pyCode, [System.Text.UTF8Encoding]::new($false))
  try {
    if ([System.IO.Path]::GetFileNameWithoutExtension($python) -ieq 'py') { & $python -3 $tempPy $tempJson } else { & $python $tempPy $tempJson }
    if ($LASTEXITCODE -ne 0) { throw "SELENIUM_159_EXIT_CODE_$LASTEXITCODE" }
    $browser = Read-Json $tempJson
  } finally {
    Remove-Item -LiteralPath $tempPy -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $tempJson -Force -ErrorAction SilentlyContinue
  }
  $browserPassed = ([string]$browser.status -eq 'PASS' -and [int]$browser.rendered_rows -ge 3 -and [bool]$browser.extended_badge_visible -and [bool]$browser.srtm30_column_visible -and [bool]$browser.aster30_column_visible -and [bool]$browser.consensus_median_visible -and [bool]$browser.source_spread_visible -and @($browser.console_errors).Count -eq 0)
  Write-Json (Join-Path $repoRoot ($browserProofRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId; page_key='topography'; status=if($browserPassed){'PASS'}else{'FAIL'}; validated_at=Now-Utc; browser=$browser; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })
  if (-not $browserPassed) { throw 'TOPOGRAPHY_159_BROWSER_ACCEPTANCE_FAILED' }
  $stages += [ordered]@{ stage='third_chrome_extended_consensus_validation'; status='PASS'; rendered_rows=[int]$browser.rendered_rows }

  # Stage 15: write consolidated status, report, site latest changes and runner output.
  $completedAt = Now-Utc
  $highConsistency = @($consensusRows | Where-Object { $_.consensus_status -eq 'HIGH_CONSISTENCY_WITHIN_3M' }).Count
  $moderateConsistency = @($consensusRows | Where-Object { $_.consensus_status -eq 'MODERATE_CONSISTENCY_WITHIN_8M' }).Count
  $manualReview = @($consensusRows | Where-Object { $_.consensus_status -match 'MANUAL_REVIEW' }).Count
  $statusPayload = [ordered]@{
    task_id=$taskId
    page_key='topography'
    status='EXTENDED_MULTI_DEM_CONSENSUS_VISIBLE_BROWSER_PASS_PRIMARY_VALIDATION_PENDING'
    started_at=$startedAt
    completed_at=$completedAt
    branch=$branch
    canonical_storage='F_PORTABLE_ROOT'
    single_runner_only=$true
    new_runner=$false
    parallel_runner=$false
    stages=$stages
    inherited_stage_count=9
    total_serial_stage_count=15
    candidate_rows=$rows.Count
    regional_control_rows=8
    eudem_source_backed_rows=$rows.Count
    srtm90_crosscheck_rows=$rows.Count
    srtm30_quality_control_rows=[int]$srtm30.result_count
    aster30_quality_control_rows=[int]$aster30.result_count
    consensus_rows=$consensusRows.Count
    high_consistency_rows=$highConsistency
    moderate_consistency_rows=$moderateConsistency
    manual_review_rows=$manualReview
    browser_rendered_rows=[int]$browser.rendered_rows
    completion_percent=$completionPercent
    percent_increase=($completionPercent - 55)
    accuracy_score_4='2.5/4 fallback multi-DEM consensus; primary CopDEM raster, real parcel boundary and official EA LiDAR/OS Terrain numeric validation pending'
    blockers=@('real_parcel_boundary_required','primary_copdem_glo30_raster_sampling_required','ea_lidar_or_os_terrain_numeric_validation_required','project_regional_average_report_required')
    final_ready=$false
    product_final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  }
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\')) $statusPayload
  Write-Json (Join-Path $repoRoot ($latestChangesRel -replace '/', '\')) ([ordered]@{
    layer='Topography'; updated_at=$completedAt; final_ready=$false; manual_review_required=$true;
    summary=[ordered]@{ completion_percent=$completionPercent; remaining_percent=(100-$completionPercent); filled_parcel_count=$rows.Count; verified_parcel_count=$rows.Count; eudem_source_backed_rows=$rows.Count; srtm90_crosscheck_rows=$rows.Count; srtm30_quality_control_rows=[int]$srtm30.result_count; aster30_quality_control_rows=[int]$aster30.result_count; consensus_rows=$consensusRows.Count; browser_visible_rows=[int]$browser.rendered_rows; accuracy_score_4='2.5/4 fallback multi-DEM consensus; primary validation pending'; website_update_percent=$completionPercent };
    blockers=$statusPayload.blockers; changes=$rows; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })

  $report = @"
# Topography 159 — Extended Multi-DEM Consensus Batch

- Candidate parcel rows: $($rows.Count)
- Regional control samples inherited: 8
- EU-DEM 25 m source-backed rows: $($rows.Count)
- SRTM 90 m cross-check rows: $($rows.Count)
- SRTM 30 m QC rows: $($srtm30.result_count)
- ASTER 30 m QC rows: $($aster30.result_count)
- Consensus rows: $($consensusRows.Count)
- High consistency rows: $highConsistency
- Moderate consistency rows: $moderateConsistency
- Manual review rows: $manualReview
- Browser rendered rows: $($browser.rendered_rows)
- Total serial stages represented: 15
- Completion percent after real runner proof: $completionPercent
- Accuracy: 2.5/4 fallback multi-DEM consensus
- final_ready: false
- fake_data: false

All work ran serially inside the existing F-portable canonical shared runner. No second or parallel runner was opened. Extra DEMs are quality-control sources only and do not promote the rows to primary or final status. Real parcel boundaries, primary CopDEM GLO-30 raster sampling and official Environment Agency LiDAR or Ordnance Survey Terrain numeric validation remain mandatory.
"@
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($reportRel -replace '/', '\')))
  [System.IO.File]::WriteAllText((Join-Path $repoRoot ($reportRel -replace '/', '\')), $report, [System.Text.UTF8Encoding]::new($false))
  Write-Json (Join-Path $repoRoot ($runnerOutputRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId; started_at=$startedAt; completed_at=$completedAt; status='COMPLETED_VISIBLE_NOT_FINAL'; stages=$stages; status_path=$statusRel; report_path=$reportRel; browser_proof_path=$browserProofRel; source_snapshot_path=$sourceSnapshotRel; consensus_rows_path=$consensusRowsRel; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })
  Write-OperationLedger -StageItems $stages -ParcelRows $rows -RunStatus 'COMPLETED_VISIBLE_NOT_FINAL'
  Write-Output ($statusPayload | ConvertTo-Json -Depth 50)
  exit 0
} catch {
  $failedAt = Now-Utc
  Write-OperationLedger -StageItems $stages -ParcelRows @() -RunStatus 'BLOCKED' -FailureBlocker $_.Exception.Message
  $failure = [ordered]@{ task_id=$taskId; page_key='topography'; status='BLOCKED_EXTENDED_MULTI_DEM_CONSENSUS_BATCH'; started_at=$startedAt; failed_at=$failedAt; error=$_.Exception.Message; stages=$stages; completion_percent=40; percent_increase=0; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\')) $failure
  Write-Json (Join-Path $repoRoot ($runnerOutputRel -replace '/', '\')) $failure
  Write-Error $_
  exit 1
}
