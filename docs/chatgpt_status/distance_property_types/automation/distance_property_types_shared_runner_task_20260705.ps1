param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [string]$TaskId = $env:AAYS_TASK_ID
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }
if ([string]::IsNullOrWhiteSpace($TaskId)) { $TaskId = 'distance_property_types_current_20260705' }
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
function D($p){ if($p -and -not(Test-Path -LiteralPath $p)){ New-Item -ItemType Directory -Force -Path $p | Out-Null } }
function W($rel,$content){ $full=Join-Path $RepoRoot ($rel -replace '/','\'); D (Split-Path -Parent $full); [System.IO.File]::WriteAllText($full,$content,[System.Text.UTF8Encoding]::new($false)) }
function J($o){ $o|ConvertTo-Json -Depth 20 }
$page='distance_property_types'
$inputRel='docs/chatgpt_status/distance_property_types/inputs/distance_property_types_source_candidates.csv'
$templateRel='docs/chatgpt_status/distance_property_types/inputs/distance_property_types_source_candidates_TEMPLATE.csv'
$reportRel='docs/chatgpt_status/distance_property_types/runner_outputs/distance_property_types_continue_verify_publish_20260704_1500.report.json'
$progressRel='docs/chatgpt_status/distance_property_types/reports/distance_property_types_progress_latest.md'
$gateRel="docs/chatgpt_status/distance_property_types/status/${TaskId}_gate.json"
$heartbeatRel="docs/chatgpt_status/distance_property_types/heartbeat/${TaskId}_heartbeat.json"
$header='parcel_id,geometry_wkt,centroid_lat,centroid_lon,candidate_property_type,official_source_evidence,web_source_evidence,map_source_evidence,photo_ai_evidence,photo_ai_image_path,photo_ai_model_or_tool,photo_ai_observation,source_date,matching_method,nearest_industrial_unit_distance_m,nearest_detached_home_distance_m,nearest_retail_property_distance_m,nearest_apartment_building_distance_m,nearest_office_building_distance_m,nearest_mixed_building_distance_m,notes'
if(-not(Test-Path -LiteralPath (Join-Path $RepoRoot ($templateRel -replace '/','\')))){ W $templateRel $header }
$inputPath=Join-Path $RepoRoot ($inputRel -replace '/','\')
$rows=@()
if(Test-Path -LiteralPath $inputPath){ try{$rows=@(Import-Csv -LiteralPath $inputPath)}catch{$rows=@()} }
$valid=@($rows|Where-Object{ $_.parcel_id -and $_.candidate_property_type -and ($_.official_source_evidence -or $_.web_source_evidence -or $_.map_source_evidence) })
$blockers=@()
if($valid.Count -eq 0){ $blockers+='missing_real_evidence_rows' }
$payload=[ordered]@{ task_id=$TaskId; page_key=$page; updated_at=(Get-Date).ToUniversalTime().ToString('s')+'Z'; queue_seen=$true; queue_started=$true; final_ready=$false; fake_data=$false; evidence_rows=$valid.Count; status=if($valid.Count){'evidence_rows_detected_manual_review_required'}else{'completed_no_real_evidence_rows'}; blockers=$blockers; CONTINUE_RUNNER_READY=$true }
W $reportRel (J $payload)
W $progressRel "# Distance Property Types runner progress`n`nfinal_ready=false`nevidence_rows=$($valid.Count)`nblockers=$($blockers -join ';')`n`nNo fake evidence was generated.`n"
W $gateRel (J ([ordered]@{task_id=$TaskId;page_key=$page;source_row_gate_passed=($valid.Count -gt 0);ui_token_gate_passed=$false;browser_smoke_passed=$false;post_sync_ok=$false;manual_review_required=$true;fake_data=$false;blockers=$blockers}))
W $heartbeatRel (J ([ordered]@{task_id=$TaskId;page_key=$page;updated_at=(Get-Date).ToUniversalTime().ToString('s')+'Z';final_ready=$false;fake_data=$false}))
Write-Output "distance_property_types_shared_task_completed final_ready=false evidence_rows=$($valid.Count)"