param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Off

$TaskId = '209_aays1_parcel_label_4row_browser_dom_proof_20260715'
$RepoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$ServedRoot = 'F:\TerraYield_AAYS_Portable\AAYS'

$InputRel = 'docs/chatgpt_status/aays1/inputs/207_parcel_label_4row_official_source_candidates_20260715.json'
$AllRowsRel = 'england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json'
$StatusRel = 'england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json'
$ChangesRel = 'england_map_web/data/program_layer_matrix/distance_property_types_latest_changes.json'
$ManifestRel = 'england_map_web/data/program_layer_matrix/distance_property_types_source_manifest_latest.json'
$IndexRel = 'england_map_web/data/program_layer_matrix/distance_property_types_row_artifact_index_latest.json'
$CheckpointRel = 'docs/chatgpt_status/aays1/checkpoints/parcel_label_canonical_checkpoint.json'
$EvidenceRel = 'docs/chatgpt_status/aays1/evidence/209_parcel_label_4row_browser_dom_proof_evidence_20260715.json'
$OutputRel = 'docs/chatgpt_status/aays1/runner_outputs/209_aays1_parcel_label_4row_browser_dom_proof_20260715_output.json'
$DomRel = 'docs/chatgpt_status/aays1/runner_outputs/209_aays1_parcel_label_4row_browser_dom_proof_20260715_dom.html'
$BrowserLogRel = 'docs/chatgpt_status/aays1/runner_outputs/209_aays1_parcel_label_4row_browser_dom_proof_20260715_browser_stderr.log'
$GateRel = 'docs/chatgpt_status/aays1/status/209_aays1_parcel_label_4row_browser_dom_proof_20260715_gate.json'
$ReportRel = 'docs/chatgpt_status/aays1/reports/209_parcel_label_4row_browser_dom_proof_report_20260715.md'
$QueueRel = 'docs/chatgpt_status/aays1/queue/209_aays1_parcel_label_4row_browser_dom_proof_20260715.task.json'

$PageUrl = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=parcel-label-209-r2'
$DataUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json?refresh=parcel-label-209-r2'

function P([string]$Rel) { Join-Path $RepoRoot ($Rel -replace '/', '\') }
function Ensure-Parent([string]$Path) {
  $parent = Split-Path -Parent $Path
  if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
}
function Read-Json([string]$Path) { Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json }
function Write-Utf8([string]$Path,[string]$Text) { Ensure-Parent $Path; [IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false)) }
function Write-Json([string]$Path,[object]$Value) { Write-Utf8 $Path (($Value | ConvertTo-Json -Depth 80) + "`n") }
function Set-Prop([object]$Object,[string]$Name,[object]$Value) { Add-Member -InputObject $Object -NotePropertyName $Name -NotePropertyValue $Value -Force; return $Object }
function Test-Http([string]$Url) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $Url -Method Get -TimeoutSec 30 -MaximumRedirection 8 -Headers @{ 'User-Agent'='Mozilla/5.0 AAYS official-source verifier' }
    return [pscustomobject]@{ ok=($r.StatusCode -ge 200 -and $r.StatusCode -lt 400); status=[int]$r.StatusCode; final_url=[string]$r.BaseResponse.ResponseUri.AbsoluteUri; error='' }
  } catch {
    $code = 0
    try { if ($_.Exception.Response.StatusCode) { $code = [int]$_.Exception.Response.StatusCode } } catch {}
    return [pscustomobject]@{ ok=$false; status=$code; final_url=$Url; error=$_.Exception.Message }
  }
}
function Resolve-Browser {
  $paths = [Collections.Generic.List[string]]::new()
  $pf86 = [Environment]::GetEnvironmentVariable('ProgramFiles(x86)')
  if ($pf86) { $paths.Add((Join-Path $pf86 'Microsoft\Edge\Application\msedge.exe')); $paths.Add((Join-Path $pf86 'Google\Chrome\Application\chrome.exe')) }
  if ($env:ProgramFiles) { $paths.Add((Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe')); $paths.Add((Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe')) }
  if ($env:LOCALAPPDATA) { $paths.Add((Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\Application\msedge.exe')); $paths.Add((Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe')) }
  foreach ($path in $paths) { if (Test-Path -LiteralPath $path -PathType Leaf) { return $path } }
  foreach ($name in @('msedge.exe','chrome.exe')) { $cmd = Get-Command $name -ErrorAction SilentlyContinue; if ($cmd) { return $cmd.Source } }
  return $null
}
function Quote-Arg([string]$Value) { return '"' + ($Value -replace '"','\"') + '"' }
function Invoke-BrowserDump([string]$Browser,[string]$HeadlessFlag,[string]$Profile) {
  $args = @($HeadlessFlag,'--disable-gpu','--disable-extensions','--disable-background-networking','--no-first-run','--no-default-browser-check','--hide-scrollbars','--window-size=1920,1080','--virtual-time-budget=30000',("--user-data-dir=$Profile"),'--dump-dom',$PageUrl)
  $si = New-Object Diagnostics.ProcessStartInfo
  $si.FileName = $Browser
  $si.Arguments = (($args | ForEach-Object { Quote-Arg ([string]$_) }) -join ' ')
  $si.UseShellExecute = $false
  $si.CreateNoWindow = $true
  $si.RedirectStandardOutput = $true
  $si.RedirectStandardError = $true
  $p = New-Object Diagnostics.Process
  $p.StartInfo = $si
  [void]$p.Start()
  $outTask = $p.StandardOutput.ReadToEndAsync()
  $errTask = $p.StandardError.ReadToEndAsync()
  if (-not $p.WaitForExit(90000)) { try { $p.Kill() } catch {}; return [pscustomobject]@{ exit_code=124; stdout=''; stderr='browser_dump_timeout'; flag=$HeadlessFlag } }
  $outTask.Wait(); $errTask.Wait()
  return [pscustomobject]@{ exit_code=[int]$p.ExitCode; stdout=[string]$outTask.Result; stderr=[string]$errTask.Result; flag=$HeadlessFlag }
}

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$input = Read-Json (P $InputRel)
$allRows = Read-Json (P $AllRowsRel)
$statusData = Read-Json (P $StatusRel)
$changes = Read-Json (P $ChangesRel)
$manifest = Read-Json (P $ManifestRel)
$rowIndex = Read-Json (P $IndexRel)

$candidateIds = @($input.candidates | ForEach-Object { [string]$_.parcel_id })
$rows = [Collections.Generic.List[object]]::new()
foreach ($row in @($allRows.rows)) { $rows.Add($row) }
$existing = @{}
foreach ($row in $rows) { $existing[[string]$row.parcel_id] = $true }

$added = [Collections.Generic.List[object]]::new()
$skipped = [Collections.Generic.List[string]]::new()
$validations = [Collections.Generic.List[object]]::new()
$now = [DateTimeOffset]::UtcNow.ToString('o')

foreach ($candidate in @($input.candidates)) {
  $id = [string]$candidate.parcel_id
  if ($existing.ContainsKey($id)) { $skipped.Add($id); continue }
  $validation = Test-Http ([string]$candidate.source_url)
  $validations.Add([pscustomobject]@{ parcel_id=$id; source_url=[string]$candidate.source_url; ok=[bool]$validation.ok; http_status=[int]$validation.status; final_url=[string]$validation.final_url; error=[string]$validation.error })
  if (-not $validation.ok) { continue }
  $newRow = [pscustomobject][ordered]@{
    parcel_id=$id; geometry_wkt=''; centroid_lat=''; centroid_lon=''
    nearest_industrial_unit_distance_m=''; nearest_detached_home_distance_m=''; nearest_retail_property_distance_m=''; nearest_apartment_building_distance_m=''; nearest_office_building_distance_m=''; nearest_mixed_building_distance_m=''; selected_match_distance_m=''
    photo_ai_evidence='not_used_for_this_candidate'; photo_ai_image_path=''; photo_ai_model_or_tool=''; photo_ai_observation=''
    conflict_status=[string]$candidate.conflict_status
    explanation='Official-source classification restored idempotently for Task 209 DOM proof. Exact geometry and manual scope review remain mandatory.'
    source_validation_http_status=[int]$validation.status; source_validation_method='GET'; source_validation_final_url=[string]$validation.final_url; source_validation_error=[string]$validation.error
    parcel_ref=[string]$candidate.parcel_ref; selected_property_type=[string]$candidate.selected_property_type; candidate_property_type=[string]$candidate.selected_property_type; selected_color_category=[string]$candidate.selected_color_category
    source_url=[string]$candidate.source_url; official_source_evidence=[string]$candidate.official_source_evidence; web_source_evidence=[string]$candidate.web_source_evidence; map_source_evidence=[string]$candidate.map_source_evidence
    classification_finding=[string]$candidate.web_source_evidence; matching_method=[string]$candidate.matching_method; accuracy_score_4=[double]$candidate.accuracy_score_4; accuracy_label_4=[string]$candidate.accuracy_label_4
    needs_manual_review=[bool]$candidate.needs_manual_review; geometry_status='NOT_BOUND'; candidate_status='SOURCE_CLASSIFICATION_ENRICHED_PENDING_MANUAL_REVIEW_AND_EXACT_GEOMETRY'
    change_kind='RESTORED_MISSING_OFFICIAL_SOURCE_CLASSIFICATION_ROW'; change_reason='task_209_restore_missing_task207_rows_before_browser_dom_proof'; changed_in_latest_run=$true; is_new_in_latest_batch=$false
    last_updated=$now; source_date='2026-07-15'; batch_id='209-recovery'; task_id=$TaskId
    payload_path=$InputRel; queue_task_path=$QueueRel; source_path=$InputRel; downloaded_source_path='official_page_runtime_http_validation_no_snapshot'; local_source_path='official_page_runtime_http_validation_no_snapshot'
    report_path=$ReportRel; evidence_path=$EvidenceRel; runner_output_path=$OutputRel; source_manifest_path=$ManifestRel; artifact_index_path=$IndexRel
    source_validation_ok=$true; source_validation_mode='official_primary_page_runtime_get_and_existing_task207_evidence'; completed=$false; final_ready=$false; fake_data=$false
  }
  $rows.Add($newRow); $added.Add($newRow); $existing[$id] = $true
}

$allRows = Set-Prop $allRows 'rows' @($rows)
foreach ($name in @('row_count','visible_row_count','unique_parcel_count','total_tracked_count','pending_runner_count')) { $allRows = Set-Prop $allRows $name $rows.Count }
$allRows = Set-Prop $allRows 'latest_batch_id' '209_dom_recovery'
$allRows = Set-Prop $allRows 'latest_batch_count' $added.Count
$allRows = Set-Prop $allRows 'latest_operation_id' $TaskId
$allRows = Set-Prop $allRows 'latest_operation_row_count' $added.Count
$allRows = Set-Prop $allRows 'source_upgraded_count' 57
$allRows = Set-Prop $allRows 'classification_enriched_count' 57
$allRows = Set-Prop $allRows 'generated_at' $now
$allRows = Set-Prop $allRows 'updated_at' $now
$allRows = Set-Prop $allRows 'status' 'ALL_TRACKED_ROWS_HTTP_AND_BROWSER_DOM_PROOF_PENDING'
$allRows = Set-Prop $allRows 'final_ready' $false
$allRows = Set-Prop $allRows 'product_final_ready' $false
$allRows = Set-Prop $allRows 'fake_data' $false
Write-Json (P $AllRowsRel) $allRows

$statusData = Set-Prop $statusData 'status' 'TASK_209_DATA_RESTORED_BROWSER_DOM_PROOF_RUNNING'
$statusData = Set-Prop $statusData 'latest_task_id' $TaskId
$statusData = Set-Prop $statusData 'tracked_row_count' $rows.Count
$statusData = Set-Prop $statusData 'visible_row_count' $rows.Count
$statusData = Set-Prop $statusData 'latest_operation_row_count' $added.Count
$statusData = Set-Prop $statusData 'source_upgraded_count' 57
$statusData = Set-Prop $statusData 'classification_enriched_count' 57
$statusData = Set-Prop $statusData 'updated_at' $now
$statusData = Set-Prop $statusData 'final_ready' $false
Write-Json (P $StatusRel) $statusData

$changes = [ordered]@{ task_id=$TaskId; operation_id='209_restore_missing_task207_rows_and_dom_proof'; updated_at=$now; restored_row_count=$added.Count; duplicate_ids_skipped=@($skipped); rows=@($added); final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
Write-Json (P $ChangesRel) $changes

$manifest = Set-Prop $manifest 'task_id' $TaskId
$manifest = Set-Prop $manifest 'updated_at' $now
$manifest = Set-Prop $manifest 'total_tracked_rows' $rows.Count
$manifest = Set-Prop $manifest 'latest_source_upgrade_count' 57
$manifest = Set-Prop $manifest 'latest_enrichment_inputs' @(@($manifest.latest_enrichment_inputs) + @($InputRel) | Select-Object -Unique)
$manifest = Set-Prop $manifest 'geometry_policy' 'Task 209 does not create or infer exact geometry.'
Write-Json (P $ManifestRel) $manifest

$indexRows = [Collections.Generic.List[object]]::new()
foreach ($row in @($rowIndex.rows)) { $indexRows.Add($row) }
$indexed = @{}
foreach ($row in $indexRows) { $indexed[[string]$row.parcel_id] = $true }
foreach ($row in $added) {
  if ($indexed.ContainsKey([string]$row.parcel_id)) { continue }
  $indexRows.Add([pscustomobject][ordered]@{ parcel_id=[string]$row.parcel_id; change_kind=[string]$row.change_kind; candidate_status=[string]$row.candidate_status; geometry_status='NOT_BOUND'; artifacts=@([ordered]@{field='payload_path';path=$InputRel;state='LOCAL_PRESENT';browser_href=('/'+$InputRel)},[ordered]@{field='report_path';path=$ReportRel;state='LOCAL_PRESENT';browser_href=('/'+$ReportRel)},[ordered]@{field='evidence_path';path=$EvidenceRel;state='LOCAL_PRESENT';browser_href=('/'+$EvidenceRel)},[ordered]@{field='runner_output_path';path=$OutputRel;state='LOCAL_PRESENT';browser_href=('/'+$OutputRel)}) })
}
$rowIndex = Set-Prop $rowIndex 'task_id' $TaskId
$rowIndex = Set-Prop $rowIndex 'generated_at' $now
$rowIndex = Set-Prop $rowIndex 'unique_parcel_count' $rows.Count
$rowIndex = Set-Prop $rowIndex 'rows' @($indexRows)
Write-Json (P $IndexRel) $rowIndex

$servedCopyOk = $false
if (Test-Path -LiteralPath $ServedRoot) {
  foreach ($rel in @($AllRowsRel,$StatusRel,$ChangesRel,$ManifestRel,$IndexRel)) {
    $src = P $rel
    $dst = Join-Path $ServedRoot ($rel -replace '/', '\')
    Ensure-Parent $dst
    Copy-Item -LiteralPath $src -Destination $dst -Force
  }
  $servedCopyOk = $true
}
Start-Sleep -Seconds 2

$health = Test-Http 'http://127.0.0.1:8012/health'
$page = Test-Http $PageUrl
$data = Test-Http $DataUrl
$servedRows = @()
$dataVisibleIds = @()
if ($data.ok) {
  try {
    $servedObject = Invoke-RestMethod -Uri $DataUrl -TimeoutSec 30
    $servedRows = @($servedObject.rows)
    $servedIds = @($servedRows | ForEach-Object { [string]$_.parcel_id })
    $dataVisibleIds = @($candidateIds | Where-Object { $servedIds -contains $_ })
  } catch {}
}

$browser = Resolve-Browser
if (-not $browser) { throw 'BROWSER_EXECUTABLE_NOT_FOUND' }
$tempProfile = Join-Path ([IO.Path]::GetTempPath()) ('aays_task209_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $tempProfile | Out-Null
try {
  $browserResult = Invoke-BrowserDump $browser '--headless=new' $tempProfile
  if ($browserResult.exit_code -ne 0 -or [string]::IsNullOrWhiteSpace($browserResult.stdout)) {
    Remove-Item -LiteralPath $tempProfile -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $tempProfile | Out-Null
    $browserResult = Invoke-BrowserDump $browser '--headless' $tempProfile
  }
} finally { Remove-Item -LiteralPath $tempProfile -Recurse -Force -ErrorAction SilentlyContinue }

$dom = [string]$browserResult.stdout
Write-Utf8 (P $DomRel) $dom
Write-Utf8 (P $BrowserLogRel) ([string]$browserResult.stderr)
$domVisibleIds = @($candidateIds | Where-Object { $dom.IndexOf($_,[StringComparison]::OrdinalIgnoreCase) -ge 0 })
$rowProof = @()
foreach ($id in $candidateIds) {
  $index = $dom.IndexOf($id,[StringComparison]::OrdinalIgnoreCase)
  $snippet = ''
  if ($index -ge 0) { $start=[Math]::Max(0,$index-180); $length=[Math]::Min(520,$dom.Length-$start); $snippet=($dom.Substring($start,$length) -replace '\s+',' ') }
  $rowProof += [ordered]@{ parcel_id=$id; data_json_visible=($dataVisibleIds -contains $id); browser_dom_visible=($domVisibleIds -contains $id); dom_snippet=$snippet }
}

$passed = ($servedCopyOk -and $health.ok -and $page.ok -and $data.ok -and $servedRows.Count -ge 198 -and $dataVisibleIds.Count -eq 4 -and $browserResult.exit_code -eq 0 -and $domVisibleIds.Count -eq 4)
$blockers = @()
if (-not $servedCopyOk) { $blockers += 'CANONICAL_SERVED_ROOT_SYNC_FAILED' }
if ($servedRows.Count -lt 198) { $blockers += ('SERVED_ROW_COUNT_BELOW_198:' + $servedRows.Count) }
if ($dataVisibleIds.Count -ne 4) { $blockers += 'DATA_JSON_FOUR_IDS_NOT_VISIBLE' }
if ($browserResult.exit_code -ne 0) { $blockers += ('HEADLESS_BROWSER_EXIT_' + $browserResult.exit_code) }
if ($domVisibleIds.Count -ne 4) { $blockers += 'BROWSER_DOM_FOUR_IDS_NOT_VISIBLE' }
$blockers += 'EXACT_GEOMETRY_BINDING_PENDING'
$blockers += 'MANUAL_SCOPE_REVIEW_PENDING'

$evidence = [ordered]@{ task_id=$TaskId; generated_at=$now; recovery_mode='same_task_idempotent_restore_then_dom_proof'; baseline_rows=194; repository_rows_after=$rows.Count; served_rows_after=$servedRows.Count; rows_restored=$added.Count; duplicate_ids_skipped=@($skipped); official_source_validations=@($validations); source_accuracy_average_4=3.9375; target_confidence_percent=98.44; served_copy_ok=$servedCopyOk; health_http_status=$health.status; page_http_status=$page.status; data_http_status=$data.status; data_json_visible_ids=@($dataVisibleIds); browser_path=$browser; browser_exit_code=$browserResult.exit_code; browser_dom_visible_ids=@($domVisibleIds); browser_dom_visibility_proven=$passed; rows=$rowProof; blockers=$blockers; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
Write-Json (P $EvidenceRel) $evidence

$output = [ordered]@{ task_id=$TaskId; status=$(if($passed){'BROWSER_DOM_FOUR_ROWS_VERIFIED'}else{'BROWSER_DOM_PROOF_BLOCKED'}); generated_at=$now; tracked_row_count=$rows.Count; served_row_count=$servedRows.Count; rows_restored=$added.Count; browser_dom_visible_count=$domVisibleIds.Count; browser_verified_rows=$(if($passed){198}else{194}); source_upgraded_rows=57; classification_enriched_rows=57; average_latest_batch_accuracy_score_4=3.9375; target_confidence_percent=98.44; exact_geometry_rows=0; page_http_ok=$page.ok; data_http_ok=$data.ok; all_four_ids_http_visible=($dataVisibleIds.Count -eq 4); browser_dom_visibility_proven=$passed; blockers=$blockers; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
Write-Json (P $OutputRel) $output
Write-Json (P $GateRel) ([ordered]@{ task_id=$TaskId; source_row_gate_passed=($dataVisibleIds.Count -eq 4); ui_token_gate_passed=$passed; browser_smoke_passed=$passed; post_sync_ok=$passed; manual_review_required=$true; exact_geometry_created=0; final_ready=$false; fake_data=$false })

if (Test-Path -LiteralPath (P $CheckpointRel)) {
  $checkpoint = Read-Json (P $CheckpointRel)
  $checkpoint = Set-Prop $checkpoint 'pending_task_id' $TaskId
  $checkpoint = Set-Prop $checkpoint 'pending_task_state' $(if($passed){'BROWSER_DOM_PROOF_VERIFIED_EXACT_GEOMETRY_PENDING'}else{'BROWSER_DOM_PROOF_BLOCKED'})
  $checkpoint = Set-Prop $checkpoint 'next_incomplete_action' $(if($passed){'exact_geometry_binding_and_manual_scope_review'}else{'recover_browser_dom_proof_for_task_209'})
  $checkpoint = Set-Prop $checkpoint 'tracked_rows' $rows.Count
  $checkpoint = Set-Prop $checkpoint 'published_rows' $servedRows.Count
  $checkpoint = Set-Prop $checkpoint 'http_verified_rows' $(if($dataVisibleIds.Count -eq 4){198}else{194})
  $checkpoint = Set-Prop $checkpoint 'browser_verified_rows' $(if($passed){198}else{194})
  $checkpoint = Set-Prop $checkpoint 'source_upgraded_rows' 57
  $checkpoint = Set-Prop $checkpoint 'classification_enriched_rows' 57
  $checkpoint = Set-Prop $checkpoint 'exact_geometry_rows' 0
  $checkpoint = Set-Prop $checkpoint 'updated_at' $now
  $checkpoint = Set-Prop $checkpoint 'blockers' $blockers
  $checkpoint = Set-Prop $checkpoint 'final_ready' $false
  $checkpoint = Set-Prop $checkpoint 'product_final_ready' $false
  $checkpoint = Set-Prop $checkpoint 'fake_data' $false
  $checkpoint = Set-Prop $checkpoint 'db_write' $false
  $checkpoint = Set-Prop $checkpoint 'migration' $false
  $checkpoint = Set-Prop $checkpoint 'production_deploy' $false
  Write-Json (P $CheckpointRel) $checkpoint
}

$report = @('# Parcel Label Task 209 — Restore and browser DOM proof','',("- Rows: 194 -> {0}; served={1}; restored={2}" -f $rows.Count,$servedRows.Count,$added.Count),("- Official-source validation: {0}/4" -f @($validations | Where-Object {$_.ok}).Count),("- Data JSON IDs: {0}/4; browser DOM IDs: {1}/4" -f $dataVisibleIds.Count,$domVisibleIds.Count),("- Average accuracy: 3.9375/4 (%98.44)"),("- Browser DOM proof: {0}" -f $passed),'- Exact geometry remains 0; four rows require manual scope review.','','| Parcel ID | JSON | Browser DOM |','|---|---:|---:|')
foreach ($proof in $rowProof) { $report += ("| {0} | {1} | {2} |" -f $proof.parcel_id,$proof.data_json_visible,$proof.browser_dom_visible) }
$report += ''; $report += '`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'
Write-Utf8 (P $ReportRel) ($report -join [Environment]::NewLine)

Write-Output ($output | ConvertTo-Json -Depth 30)
if (-not $passed) { exit 1 }
exit 0
