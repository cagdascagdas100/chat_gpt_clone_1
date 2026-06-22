param([string]$WorktreeRoot="")
$ErrorActionPreference="Stop"
$pageKey="security_public_safety_low_credit_20260612"
$taskId="terrayield-050-security-single-runner-contract-alignment"
$cycle="cycle050"
function WriteText([string]$Path,[string]$Text){$dir=Split-Path -Parent $Path;if($dir){New-Item -ItemType Directory -Force -Path $dir|Out-Null};$utf8=New-Object System.Text.UTF8Encoding($false);[IO.File]::WriteAllText($Path,$Text,$utf8)}
function Code([string]$Url){try{(Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 15).StatusCode}catch{"ERR"}}
if(-not $WorktreeRoot){$WorktreeRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path}
$runtime=Join-Path $WorktreeRoot "terrayield_land_intelligence";if(!(Test-Path $runtime)){$runtime=$WorktreeRoot}
$webRoot=@((Join-Path $runtime "england_map_web"),(Join-Path $WorktreeRoot "england_map_web"))|Where-Object{Test-Path $_}|Select-Object -First 1
$statusRoot=Join-Path $WorktreeRoot "docs\chatgpt_status\$pageKey\status"
$reportRoot=Join-Path $WorktreeRoot "docs\chatgpt_status\$pageKey\reports"
$outRoot=Join-Path $WorktreeRoot "docs\chatgpt_status\$pageKey\runner_outputs"
$heartRoot=Join-Path $WorktreeRoot "docs\chatgpt_status\$pageKey\heartbeat"
@($statusRoot,$reportRoot,$outRoot,$heartRoot)|ForEach-Object{New-Item -ItemType Directory -Force -Path $_|Out-Null}
$stamp=Get-Date -Format yyyyMMdd_HHmmss
$applyReport=Join-Path $reportRoot "050_single_runner_apply_$stamp.md"
$smokeReport=Join-Path $reportRoot "050_smoke_$stamp.md"
$fieldReport=Join-Path $reportRoot "050_field_contract_$stamp.json"
$blockerReport=Join-Path $reportRoot "050_blockers_$stamp.md"
$runnerOutput=Join-Path $outRoot "050_runner_output_$stamp.log"
$required=@("parcel_id","security_score","security_level","security_level_label","security_color_category","security_color_hex","source_name","source_url","source_date","evidence","matching_method","calculation_explanation","confidence_score","accuracy_rating")
$blockers=New-Object System.Collections.Generic.List[string]
$polygonCount=0;$pointCount=0;$contractOk=$false;$missing=@($required)
if(-not $webRoot){$blockers.Add("missing_england_map_web")}else{
  $current=Join-Path $webRoot "data\parcel_security_scores_rechecked_0_120m_spatial.geojson"
  $canonical=Join-Path $webRoot "data\parcel_security_scores_canonical_polygons.geojson"
  if(!(Test-Path (Join-Path $webRoot "app.js"))){$blockers.Add("missing_app_js")}
  if(!(Test-Path (Join-Path $webRoot "security_overlay.js"))){$blockers.Add("missing_security_overlay_js")}
  if(!(Test-Path (Join-Path $webRoot "security_overlay.css"))){$blockers.Add("missing_security_overlay_css")}
  $probeFile=$null;if(Test-Path $canonical){$probeFile=$canonical}elseif(Test-Path $current){$probeFile=$current}else{$blockers.Add("missing_security_geojson")}
  if($probeFile){
    $obj=Get-Content -Raw $probeFile|ConvertFrom-Json
    foreach($f in @($obj.features)){
      $t=$f.geometry.type
      if($t -eq "Point"){$pointCount++}
      if($t -eq "Polygon" -or $t -eq "MultiPolygon"){$polygonCount++}
      $props=$f.properties
      if($props){$m=@();foreach($k in $required){if($null -eq $props.$k -or [string]$props.$k -eq ""){$m+=$k}};if($m.Count -lt $missing.Count){$missing=$m};if($m.Count -eq 0){$contractOk=$true}}
    }
  }
}
if($polygonCount -le 0){$blockers.Add("no_polygon_or_multipolygon_feature")}
if(-not $contractOk){$blockers.Add("canonical_contract_incomplete")}
$health=Code "http://127.0.0.1:8010/health";$app=Code "http://127.0.0.1:8010/england_map_web/";$js=Code "http://127.0.0.1:8010/england_map_web/security_overlay.js";$css=Code "http://127.0.0.1:8010/england_map_web/security_overlay.css"
WriteText $smokeReport "# 050 smoke`ngenerated_at: $((Get-Date).ToString('s'))`nhealth_status: $health`napp_status: $app`nsecurity_js_status: $js`nsecurity_css_status: $css`n"
$fieldObj=@{generated_at=(Get-Date).ToString("o");cycle=$cycle;web_root=$webRoot;point_feature_count=$pointCount;polygon_feature_count=$polygonCount;contract_fields_complete=$contractOk;missing_fields=$missing;blockers=@($blockers|Select-Object -Unique)}
WriteText $fieldReport ($fieldObj|ConvertTo-Json -Depth 10)
$unique=@($blockers|Select-Object -Unique);$ready=($unique.Count -eq 0);$percent=if($ready){100}else{86};$decision=if($ready){"FINAL_READY_PARCEL_ACCEPTANCE"}else{"BLOCKED_MISSING_REAL_PARCEL_CARRIER_OR_CANONICAL_FIELDS"}
$blockText="# 050 blockers`nfinal_decision: $decision`n";if($unique.Count){$unique|ForEach-Object{$blockText+="- $_`n"}}else{$blockText+="- none`n"};WriteText $blockerReport $blockText
WriteText $applyReport "# 050 apply report`ngenerated_at: $((Get-Date).ToString('s'))`nstatus: $(if($ready){'READY'}else{'BLOCKED'})`ncompletion_percent: $percent`nfinal_decision: $decision`nworktree_root: $WorktreeRoot`nweb_root: $webRoot`nfield_contract_report: $fieldReport`nsmoke_report: $smokeReport`nblocker_report: $blockerReport`nrunner_output: $runnerOutput`nseparate_runner_required: false`npowershell_required_from_user: false`n"
WriteText $runnerOutput "task_id: $taskId`ncycle: $cycle`nscript_path: docs/chatgpt_status/$pageKey/automation/vrun.ps1`nworktree_root: $WorktreeRoot`nweb_root: $webRoot`nfinal_decision: $decision`n"
# Compatibility aliases for stale runner_tasks/current-task.json that still expects 049_* outputs.
Copy-Item -Force $applyReport (Join-Path $reportRoot "049_single_runner_apply_$stamp.md")
Copy-Item -Force $fieldReport (Join-Path $reportRoot "049_field_contract_$stamp.json")
Copy-Item -Force $smokeReport (Join-Path $reportRoot "049_smoke_$stamp.md")
Copy-Item -Force $blockerReport (Join-Path $reportRoot "049_blockers_$stamp.md")
Copy-Item -Force $runnerOutput (Join-Path $outRoot "049_runner_output_$stamp.log")
WriteText (Join-Path $statusRoot "latest.json") (@{page_key=$pageKey;task_id=$taskId;cycle=$cycle;current_status=if($ready){"READY"}else{"BLOCKED"};completion_percent=$percent;final_ready=$ready;remaining_blockers=$unique;latest_final_report=$applyReport;latest_smoke_report=$smokeReport;latest_runner_output=$runnerOutput;updated_at=(Get-Date).ToString("o");db_write=$false;ddl=$false;migration=$false;production_deploy=$false;separate_runner_required=$false;powershell_required_from_user=$false;runner_tasks_049_aliases_written=$true;next_user_message="devam et"}|ConvertTo-Json -Depth 10)
WriteText (Join-Path $heartRoot "latest.json") (@{page_key=$pageKey;task_id=$taskId;cycle=$cycle;status=if($ready){"READY"}else{"BLOCKED"};completion_percent=$percent;updated_at=(Get-Date).ToString("o");latest_runner_output=$runnerOutput;runner_tasks_049_aliases_written=$true}|ConvertTo-Json -Depth 8)
Write-Output $runnerOutput
if($ready){exit 0}else{exit 2}
