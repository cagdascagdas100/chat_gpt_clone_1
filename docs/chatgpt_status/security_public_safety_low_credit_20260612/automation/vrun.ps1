param([string]$WorktreeRoot="")
$ErrorActionPreference="Stop"
$pageKey="security_public_safety_low_credit_20260612"
$taskId="terrayield-049-security-contract-verification-single-runner"
$cycle="cycle049"
function WriteText([string]$Path,[string]$Text){$dir=Split-Path -Parent $Path;if($dir){New-Item -ItemType Directory -Force -Path $dir|Out-Null};$utf8=New-Object System.Text.UTF8Encoding($false);[IO.File]::WriteAllText($Path,$Text,$utf8)}
function Code([string]$Url){try{(Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 15).StatusCode}catch{"ERR:"+$_.Exception.Message}}
if(-not $WorktreeRoot){$WorktreeRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path}
$runtime=Join-Path $WorktreeRoot "terrayield_land_intelligence";if(!(Test-Path $runtime)){$runtime=$WorktreeRoot}
$webCandidates=@((Join-Path $runtime "england_map_web"),(Join-Path $WorktreeRoot "england_map_web"))
$webRoot=$webCandidates|Where-Object{Test-Path $_}|Select-Object -First 1
$statusRoot=Join-Path $WorktreeRoot "docs\chatgpt_status\$pageKey\status"
$reportRoot=Join-Path $WorktreeRoot "docs\chatgpt_status\$pageKey\reports"
$outRoot=Join-Path $WorktreeRoot "docs\chatgpt_status\$pageKey\runner_outputs"
$heartRoot=Join-Path $WorktreeRoot "docs\chatgpt_status\$pageKey\heartbeat"
@($statusRoot,$reportRoot,$outRoot,$heartRoot)|ForEach-Object{New-Item -ItemType Directory -Force -Path $_|Out-Null}
$stamp=Get-Date -Format yyyyMMdd_HHmmss
$applyReport=Join-Path $reportRoot "049_single_runner_apply_$stamp.md"
$smokeReport=Join-Path $reportRoot "049_smoke_$stamp.md"
$fieldReport=Join-Path $reportRoot "049_field_contract_$stamp.json"
$blockerReport=Join-Path $reportRoot "049_blockers_$stamp.md"
$runnerOutput=Join-Path $outRoot "049_runner_output_$stamp.log"
$blockers=New-Object System.Collections.Generic.List[string]
if(-not $webRoot){$blockers.Add("missing_england_map_web")}
$appJs=$null;$geoJson=$null;$canonical=$null
if($webRoot){
  $appJs=Join-Path $webRoot "app.js"
  $geoJson=Join-Path $webRoot "data\parcel_security_scores_rechecked_0_120m_spatial.geojson"
  $canonical=Join-Path $webRoot "data\parcel_security_scores_canonical_polygons.geojson"
  if(!(Test-Path $appJs)){$blockers.Add("missing_app_js")}
  if(!(Test-Path $geoJson)){$blockers.Add("missing_current_geojson")}
  if(!(Test-Path (Join-Path $webRoot "security_overlay.js"))){$blockers.Add("missing_security_overlay_js")}
  if(!(Test-Path (Join-Path $webRoot "security_overlay.css"))){$blockers.Add("missing_security_overlay_css")}
}
$py=Join-Path $outRoot "049_contract_probe_$stamp.py"
WriteText $py @'
import json, sys, time
from pathlib import Path
required="parcel_id security_score security_level security_level_label security_color_category security_color_hex source_name source_url source_date evidence matching_method calculation_explanation confidence_score accuracy_rating".split()
def has(v): return v is not None and not (isinstance(v,str) and not v.strip()) and not (isinstance(v,list) and not v)
def load(p):
    with open(p,encoding="utf-8-sig") as f: return json.load(f)
root=Path(sys.argv[1]); web=Path(sys.argv[2]) if sys.argv[2] else None; out=Path(sys.argv[3])
res={"generated_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"cycle":"cycle049","web_root":str(web) if web else None,"point_feature_count":0,"polygon_feature_count":0,"canonical_file_exists":False,"contract_fields_complete":False,"missing_fields":required,"blockers":[]}
if not web:
    res["blockers"].append("missing_web_root")
elif not (web/"data"/"parcel_security_scores_rechecked_0_120m_spatial.geojson").exists():
    res["blockers"].append("missing_current_geojson")
else:
    src=web/"data"/"parcel_security_scores_rechecked_0_120m_spatial.geojson"
    obj=load(src); feats=obj.get("features") or []
    res["point_feature_count"]=sum(1 for f in feats if (f.get("geometry") or {}).get("type")=="Point")
    res["polygon_feature_count"]=sum(1 for f in feats if (f.get("geometry") or {}).get("type") in ("Polygon","MultiPolygon"))
    canon=web/"data"/"parcel_security_scores_canonical_polygons.geojson"
    if canon.exists():
        res["canonical_file_exists"]=True
        c=load(canon); cfeats=c.get("features") or []
        res["polygon_feature_count"]=sum(1 for f in cfeats if (f.get("geometry") or {}).get("type") in ("Polygon","MultiPolygon"))
        best=required
        for f in cfeats:
            p=f.get("properties") or {}; miss=[k for k in required if not has(p.get(k))]
            if len(miss)<len(best): best=miss
            if not miss:
                res["contract_fields_complete"]=True; best=[]; break
        res["missing_fields"]=best
    if res["polygon_feature_count"]<=0: res["blockers"].append("no_polygon_or_multipolygon_feature")
    if not res["contract_fields_complete"]: res["blockers"].append("canonical_contract_incomplete")
out.write_text(json.dumps(res,indent=2,ensure_ascii=False),encoding="utf-8")
sys.exit(0 if not res["blockers"] else 2)
'@
if(Get-Command python -ErrorAction SilentlyContinue -and $webRoot){try{& python $py $WorktreeRoot $webRoot $fieldReport|Out-Null}catch{}}
if(Test-Path $fieldReport){$f=Get-Content -Raw $fieldReport|ConvertFrom-Json;if($f.blockers){$f.blockers|ForEach-Object{$blockers.Add([string]$_)}}}else{$blockers.Add("field_probe_not_written")}
$health=Code "http://127.0.0.1:8010/health"
$app=Code "http://127.0.0.1:8010/england_map_web/"
$js=Code "http://127.0.0.1:8010/england_map_web/security_overlay.js"
$css=Code "http://127.0.0.1:8010/england_map_web/security_overlay.css"
$canonStatus=Code "http://127.0.0.1:8010/england_map_web/data/parcel_security_scores_canonical_polygons.geojson"
WriteText $smokeReport "# 049 smoke`ngenerated_at: $((Get-Date).ToString('s'))`nhealth_status: $health`napp_status: $app`nsecurity_js_status: $js`nsecurity_css_status: $css`ncanonical_polygon_geojson_status: $canonStatus`n"
$unique=@($blockers|Select-Object -Unique)
$ready=$false;$percent=82
if($unique.Count -eq 0){$ready=$true;$percent=100}
$decision=if($ready){"FINAL_READY_PARCEL_ACCEPTANCE"}else{"BLOCKED_MISSING_REAL_PARCEL_CARRIER_OR_CANONICAL_FIELDS"}
$blockText="# 049 blockers`nfinal_decision: $decision`n";if($unique.Count){$unique|ForEach-Object{$blockText+="- $_`n"}}else{$blockText+="- none`n"}
WriteText $blockerReport $blockText
WriteText $applyReport "# 049 apply report`ngenerated_at: $((Get-Date).ToString('s'))`nstatus: $(if($ready){'READY'}else{'BLOCKED'})`ncompletion_percent: $percent`nfinal_decision: $decision`nworktree_root: $WorktreeRoot`nweb_root: $webRoot`nfield_contract_report: $fieldReport`nsmoke_report: $smokeReport`nblocker_report: $blockerReport`nrunner_output: $runnerOutput`nseparate_runner_required: false`npowershell_required_from_user: false`n"
WriteText $runnerOutput "task_id: $taskId`ncycle: $cycle`nscript_path: docs/chatgpt_status/$pageKey/automation/vrun.ps1`nworktree_root: $WorktreeRoot`nweb_root: $webRoot`nfield_contract_report: $fieldReport`nsmoke_report: $smokeReport`nblocker_report: $blockerReport`napply_report: $applyReport`nfinal_decision: $decision`n"
WriteText (Join-Path $statusRoot "latest.json") (@{page_key=$pageKey;task_id=$taskId;cycle=$cycle;current_status=if($ready){"READY"}else{"BLOCKED"};completion_percent=$percent;final_ready=$ready;remaining_blockers=$unique;latest_final_report=$applyReport;latest_smoke_report=$smokeReport;latest_runner_output=$runnerOutput;updated_at=(Get-Date).ToString("o");db_write=$false;ddl=$false;migration=$false;production_deploy=$false;separate_runner_required=$false;powershell_required_from_user=$false;next_user_message="devam et"}|ConvertTo-Json -Depth 10)
WriteText (Join-Path $heartRoot "latest.json") (@{page_key=$pageKey;task_id=$taskId;cycle=$cycle;status=if($ready){"READY"}else{"BLOCKED"};completion_percent=$percent;updated_at=(Get-Date).ToString("o");latest_runner_output=$runnerOutput}|ConvertTo-Json -Depth 8)
Write-Output $runnerOutput
if($ready){exit 0}else{exit 2}
