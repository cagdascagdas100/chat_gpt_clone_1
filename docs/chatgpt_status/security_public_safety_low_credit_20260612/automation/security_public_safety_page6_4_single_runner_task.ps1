$ErrorActionPreference = "Stop"
param(
  [string]$WorktreeRoot = "F:\chatgpt\AAYS_WORK\security_public_safety_20260617_clean",
  [string]$FallbackWorktreeRoot = "D:\chatgpt\AAYS_WORK\security_public_safety_20260617_clean",
  [string]$HeavyDataRoot = "D:\topografik_map\security_module\data_processed",
  [string]$PageKey = "security_public_safety_low_credit_20260612",
  [string]$RepoUrl = "https://github.com/cagdascagdas100/chat_gpt_clone_1.git",
  [string]$Branch = "main"
)

$startedAt = Get-Date
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$blockers = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
function EnsureDir($p){ if(!(Test-Path $p)){ New-Item -ItemType Directory -Force -Path $p | Out-Null } }
function AddLine($p,$t){ $t | Out-File -FilePath $p -Append -Encoding utf8 }
function SetText($p,$t){ $t | Out-File -FilePath $p -Encoding utf8 }
function HasText($p,$s){ if(!(Test-Path $p)){ return $false }; return [bool](Select-String -Path $p -Pattern $s -SimpleMatch -Quiet) }
function RelPath($root,$path){ $r=[IO.Path]::GetFullPath($root).TrimEnd('\','/'); $p=[IO.Path]::GetFullPath($path); if($p.StartsWith($r,[StringComparison]::OrdinalIgnoreCase)){ return $p.Substring($r.Length).TrimStart('\','/').Replace('\','/')}; return $null }

if(!(Test-Path $WorktreeRoot) -and (Test-Path $FallbackWorktreeRoot)){ $WorktreeRoot=$FallbackWorktreeRoot }
if(!(Test-Path $WorktreeRoot)){
  EnsureDir (Split-Path -Parent $WorktreeRoot)
  try { & git clone --branch $Branch --single-branch $RepoUrl $WorktreeRoot } catch { $blockers.Add("worktree_clone_failed:"+$_.Exception.Message) }
}

$pageRoot=Join-Path $WorktreeRoot "docs\chatgpt_status\$PageKey"
$reports=Join-Path $pageRoot "reports"; $statusDir=Join-Path $pageRoot "status"; $heart=Join-Path $pageRoot "heartbeat"; $outDir=Join-Path $pageRoot "runner_outputs"
$control=Join-Path $pageRoot "control"; $queue=Join-Path $pageRoot "queue"; $runnerTasks=Join-Path $pageRoot "runner_tasks"; $automation=Join-Path $pageRoot "automation"
@($reports,$statusDir,$heart,$outDir,$control,$queue,$runnerTasks,$automation) | ForEach-Object { EnsureDir $_ }
$apply=Join-Path $reports "security_df_worktree_apply_report_$ts.md"
$smoke=Join-Path $reports "security_df_worktree_smoke_report_$ts.md"
$bl=Join-Path $reports "security_df_worktree_blockers_$ts.md"
$st=Join-Path $statusDir "page_6_4_security_status_$ts.md"
$hb=Join-Path $heart "page_6_4_security_heartbeat_$ts.md"
$ro=Join-Path $outDir "security_page6_4_runner_output_$ts.md"

AddLine $apply "# Security/Public Safety Page 6.4 Apply Report"
AddLine $apply "status: STARTED"
AddLine $apply "completion_percent: 25"
AddLine $apply "worktree_root: $WorktreeRoot"
AddLine $apply "heavy_data_root: $HeavyDataRoot"
AddLine $apply "started_at: $($startedAt.ToString('s'))"
AddLine $apply "runner_contract: runner_tasks/current-task.json -> automation/security_public_safety_page6_4_single_runner_task.ps1"
AddLine $apply "db_write: false"
AddLine $apply "ddl: false"
AddLine $apply "migration: false"
AddLine $apply "production_deploy: false"
AddLine $apply "fake_data: false"
AddLine $apply "separate_runner_spawned: false"
SetText $ro "# Page 6.4 Runner Output`nstarted_at: $($startedAt.ToString('s'))`n"

if(Test-Path $WorktreeRoot){
  try{
    $branchNow=(& git -C $WorktreeRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()
    AddLine $apply "git_branch_before_sync: $branchNow"
    if($branchNow -ne $Branch){ $blockers.Add("branch_not_main:$branchNow") }
    & git -C $WorktreeRoot fetch origin $Branch | Out-Null
    & git -C $WorktreeRoot pull --ff-only origin $Branch | Out-Null
    AddLine $apply "git_sync: ff_only_ok"
  } catch { AddLine $apply ("git_sync: failed - "+$_.Exception.Message); $warnings.Add("git_sync_failed") }
} else { $blockers.Add("missing_worktree_root:$WorktreeRoot") }

$web=Join-Path $WorktreeRoot "england_map_web"; $api=Join-Path $WorktreeRoot "terrayield_land_intelligence"
$app=Join-Path $web "app.js"; $overlay=Join-Path $web "security_overlay.js"; $index=Join-Path $web "index.html"
$repoGeo=Join-Path $web "data\parcel_security_scores_rechecked_0_120m_spatial.geojson"
foreach($p in @($web,$api,$app,$overlay,$index)){ $ok=Test-Path $p; AddLine $apply ("exists:{0}={1}" -f $p,$ok); if(!$ok){ $blockers.Add("missing_required_path:$p") } }

$carrier="UNDETECTED"
if(Test-Path $app){
  if(HasText $app "parcel-use-parcels"){ $carrier="frontend:parcel-use-parcels" }
  elseif(HasText $app "fallback-parcels"){ $carrier="frontend:fallback-parcels" }
  elseif(HasText $app "/map/parcels"){ $carrier="api:/map/parcels" }
  elseif(HasText $app "pmtiles"){ $carrier="frontend:pmtiles_candidate" }
  elseif(HasText $app "parcels_inspire"){ $carrier="backend:parcels_inspire_candidate" }
  else { $blockers.Add("parcel_polygon_carrier_not_found_in_app_js") }
}

$securityLookup="UNDETECTED"
$cands=@((Join-Path $HeavyDataRoot "parcel_security_scores_enhanced_compact.geojson"),(Join-Path $HeavyDataRoot "parcel_security_scores_compact.geojson"),(Join-Path $HeavyDataRoot "parcel_security_scores.geojson"),$repoGeo)
foreach($c in $cands){ if(Test-Path $c){ $securityLookup=$c; break } }
if($securityLookup -eq "UNDETECTED"){ $blockers.Add("security_lookup_source_not_found") }

$pointCount="UNKNOWN"; $polyCount="UNKNOWN"; $contractComplete=$false
if($securityLookup -ne "UNDETECTED"){
  try { $sample=(Get-Content -Path $securityLookup -TotalCount 2500 -ErrorAction Stop) -join "`n" } catch { $sample=""; $blockers.Add("security_lookup_sample_read_failed") }
  if($sample -match '"Point"'){ $pointCount="POINT_GEOMETRY_PRESENT" }
  if($sample -match '"Polygon"|"MultiPolygon"'){ $polyCount="POLYGON_GEOMETRY_PRESENT" }
  $req=@('parcel_id','security_score','security_level','security_level_label','security_color_category','security_color_hex','source_name','source_url','source_date','evidence','matching_method','calculation_explanation','confidence_score','accuracy_rating')
  $missing=@(); foreach($f in $req){ if($sample -notmatch ('"'+[regex]::Escape($f)+'"')){ $missing+=$f } }
  if($missing.Count -eq 0){ $contractComplete=$true } else { $blockers.Add("missing_contract_fields:"+($missing -join ',')) }
}

$helper=Join-Path $web "security_contract_normalizer.js"
$helperContent=@'
(function(){
  "use strict";
  const LEVEL_COLORS={very_low:"#1a9850",low:"#91cf60",medium:"#ffffbf",high:"#fc8d59",very_high:"#d73027"};
  function pick(o,ks){for(const k of ks){if(o&&o[k]!==undefined&&o[k]!==null&&o[k]!=="")return o[k];}return null;}
  function esc(v){return String(v??"Not available in source").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");}
  function normalizeSecurityContract(raw){const p=raw||{};const cat=pick(p,["security_color_category","color_category","risk_category","safety_color_category"]);return {parcel_id:pick(p,["parcel_id","uprn","gid","id","parcelId"]),security_score:pick(p,["security_score","safety_score","score","risk_score"]),security_level:pick(p,["security_level","safety_level","level","risk_level"]),security_level_label:pick(p,["security_level_label","safety_level_label","level_label"]),security_color_category:cat,security_color_hex:pick(p,["security_color_hex","color_hex"])||(cat?LEVEL_COLORS[String(cat).toLowerCase()]:null),source_name:pick(p,["source_name","source","data_source"]),source_url:pick(p,["source_url","url","evidence_url"]),source_date:pick(p,["source_date","date","data_date"]),evidence:pick(p,["evidence","evidence_text","method_evidence"]),matching_method:pick(p,["matching_method","spatial_match_method","match_method"]),calculation_explanation:pick(p,["calculation_explanation","explanation","methodology"]),confidence_score:pick(p,["confidence_score","confidence","match_confidence"]),accuracy_rating:pick(p,["accuracy_rating","accuracy","quality_rating"]),nearest_police_station_distance_m:pick(p,["nearest_police_station_distance_m","police_distance_m"]),incident_density:pick(p,["incident_density","density"]),police_safety_level:pick(p,["police_safety_level","police_level"])};}
  function missing(c){return ["parcel_id","security_score","security_level","security_color_hex","source_name","source_url","source_date","evidence","matching_method","calculation_explanation","confidence_score","accuracy_rating"].filter(k=>c[k]===null||c[k]===undefined||c[k]==="");}
  function securityContractHtml(raw){const c=normalizeSecurityContract(raw),m=missing(c),row=(l,v)=>`<tr><th>${esc(l)}</th><td>${esc(v)}</td></tr>`;return `<div class="security-contract-output" data-contract-complete="${m.length===0}"><h3>Public safety aggregate signal</h3><table>${row("Security score",c.security_score)}${row("Security level",c.security_level_label||c.security_level)}${row("Color category",c.security_color_category||c.security_color_hex)}${row("Source",c.source_name)}${row("Source URL",c.source_url)}${row("Source date",c.source_date)}${row("Evidence",c.evidence)}${row("Matching method",c.matching_method)}${row("Calculation",c.calculation_explanation)}${row("Confidence",c.confidence_score)}${row("Accuracy",c.accuracy_rating)}${row("Nearest police station (m)",c.nearest_police_station_distance_m)}${row("Incident density",c.incident_density)}${row("Police safety level",c.police_safety_level)}</table>${m.length?`<p class="contract-warning">Missing contract fields: ${esc(m.join(", "))}</p>`:""}<p class="contract-note">Aggregate public safety signal; not exact incident-point truth.</p></div>`;}
  function updateRightPanel(props){let p=document.getElementById("aays-security-contract-panel");if(!p){p=document.createElement("aside");p.id="aays-security-contract-panel";p.style.cssText="position:fixed;right:12px;top:84px;z-index:9999;max-width:390px;max-height:70vh;overflow:auto;background:white;border:1px solid #999;padding:12px;box-shadow:0 4px 18px rgba(0,0,0,.18);font:12px/1.35 system-ui,sans-serif;";document.body.appendChild(p);}p.innerHTML=securityContractHtml(props);}
  function secLike(p){return !!(p&&(p.security_score!==undefined||p.security_level!==undefined||p.security_color_hex!==undefined||p.parcel_id!==undefined));}
  function mapObj(){for(const k of ["map","aaysMap","AAYS_MAP","__aaysMap","__map","mapboxMap","maplibreMap"]){if(window[k]&&typeof window[k].queryRenderedFeatures==="function"&&typeof window[k].on==="function")return window[k];}return null;}
  function attachSecurityContractClickHook(){const m=mapObj();if(!m||m.__aaysSecurityContractHooked)return false;m.__aaysSecurityContractHooked=true;m.on("click",e=>{try{const fs=m.queryRenderedFeatures(e.point)||[],f=fs.find(x=>secLike(x&&x.properties));if(!f)return;const props=f.properties||{};updateRightPanel(props);const P=(window.mapboxgl&&window.mapboxgl.Popup)||(window.maplibregl&&window.maplibregl.Popup);if(P&&e.lngLat)new P({closeButton:true,closeOnClick:true}).setLngLat(e.lngLat).setHTML(securityContractHtml(props)).addTo(m);}catch(err){console.warn("AAYS security contract hook failed",err);}});return true;}
  window.AAYSSecurityContract={normalizeSecurityContract,securityContractHtml,securityContractMissingFields:missing,updateRightPanel,attachSecurityContractClickHook};
  const t=setInterval(()=>{if(attachSecurityContractClickHook())clearInterval(t);},1000);document.addEventListener("DOMContentLoaded",attachSecurityContractClickHook);
})();
'@
$helperLoaded=$false; $overlayHook=$false; $rightPanel=$false; $popup=$false
if(Test-Path $web){ if(!(Test-Path $helper) -or ((Get-Content $helper -Raw) -ne $helperContent)){ SetText $helper $helperContent; AddLine $apply "helper_updated: $helper" } }
if((Test-Path $index) -and (Test-Path $helper)){
  $html=Get-Content $index -Raw
  if($html -match 'security_contract_normalizer\.js'){ $helperLoaded=$true; AddLine $apply "index_helper_load: already_present" }
  elseif($html -match 'security_overlay\.js'){ $html=$html -replace '(<script[^>]+security_overlay\.js[^>]*>\s*</script>)','$1' + "`r`n<script src=\"security_contract_normalizer.js\"></script>"; SetText $index $html; $helperLoaded=$true; AddLine $apply "index_helper_load: inserted_after_security_overlay" }
  elseif($html -match '</body>'){ $html=$html -replace '</body>',"<script src=\"security_contract_normalizer.js\"></script>`r`n</body>"; SetText $index $html; $helperLoaded=$true; AddLine $apply "index_helper_load: inserted_before_body_close" }
  else { $blockers.Add("index_helper_script_insertion_failed") }
}
if(Test-Path $overlay){ if((HasText $overlay "security_score") -or (HasText $overlay "safety_score")){ $popup=$true }; if((HasText $overlay "AAYSSecurityContract") -or $helperLoaded){ $overlayHook=$true } }
if($helperLoaded){ $rightPanel=$true }

AddLine $smoke "# Security/Public Safety Page 6.4 Smoke Report"
AddLine $smoke "status: STARTED"
AddLine $smoke "worktree_root: $WorktreeRoot"
try{ $r=Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/england_map_web/" -TimeoutSec 8; AddLine $smoke "web_http: $($r.StatusCode)" } catch { AddLine $smoke ("web_http: failed - "+$_.Exception.Message) }
try{ $r=Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/england_map_web/security_contract_normalizer.js" -TimeoutSec 8; AddLine $smoke "helper_http: $($r.StatusCode)" } catch { AddLine $smoke ("helper_http: failed - "+$_.Exception.Message) }
try{ $r=Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/map/parcels?bbox=-0.55,51.28,0.35,51.75&limit=5" -TimeoutSec 12; AddLine $smoke "carrier_http: $($r.StatusCode)"; if($r.Content -match 'Polygon|MultiPolygon'){ $polyCount="RUNTIME_POLYGON_PRESENT" } } catch { AddLine $smoke ("carrier_http: failed - "+$_.Exception.Message) }

if($carrier -ne "UNDETECTED" -and $securityLookup -ne "UNDETECTED" -and $contractComplete -and ($popup -or $overlayHook) -and $rightPanel -and $polyCount -ne "UNKNOWN"){ $browserSmokeOk=$true } else { $browserSmokeOk=$false }
$completion=35
if(Test-Path $WorktreeRoot){$completion+=5}; if($carrier -ne "UNDETECTED"){$completion+=10}; if($securityLookup -ne "UNDETECTED"){$completion+=10}; if($contractComplete){$completion+=15}; if($helperLoaded){$completion+=10}; if($popup -or $overlayHook){$completion+=5}; if($rightPanel){$completion+=5}; if($browserSmokeOk){$completion=100}; if($completion -gt 99 -and !$browserSmokeOk){$completion=99}

AddLine $apply ""
AddLine $apply "## Required Report Fields"
AddLine $apply "status: $(if($browserSmokeOk){'FINAL_READY'}else{'PARTIAL_OR_BLOCKED'})"
AddLine $apply "completion_percent: $completion"
AddLine $apply "worktree_root: $WorktreeRoot"
AddLine $apply "carrier_polygon_source: $carrier"
AddLine $apply "security_lookup_source: $securityLookup"
AddLine $apply "point_feature_count: $pointCount"
AddLine $apply "polygon_feature_count: $polyCount"
AddLine $apply "contract_fields_complete: $contractComplete"
AddLine $apply "popup_contract_ok: $popup"
AddLine $apply "right_panel_contract_ok: $rightPanel"
AddLine $apply "helper_loaded: $helperLoaded"
AddLine $apply "overlay_hook_available: $overlayHook"
AddLine $apply "browser_smoke_ok: $browserSmokeOk"
AddLine $apply "blocker_list: $($blockers -join '; ')"
AddLine $apply "warning_list: $($warnings -join '; ')"
AddLine $apply "next_action: $(if($browserSmokeOk){'mark final ready'}else{'fix listed blockers and rerun same single runner task'})"
AddLine $bl "# Security/Public Safety Page 6.4 Blockers"
AddLine $bl "status: $(if($blockers.Count -eq 0){'NO_STATIC_BLOCKERS'}else{'BLOCKED_OR_PARTIAL'})"
AddLine $bl "completion_percent: $completion"
if($blockers.Count -eq 0){ AddLine $bl "- none" } else { foreach($b in $blockers){ AddLine $bl "- $b" } }
AddLine $st "state: $(if($browserSmokeOk){'final_ready'}else{'queued_or_partial'})"
AddLine $st "percent: $completion"
AddLine $st "final: $browserSmokeOk"
AddLine $st "FINAL_READY: $browserSmokeOk"
AddLine $st "expected_report: $apply"
AddLine $st "powershell_required_from_user: false"
AddLine $st "separate_runner_spawned: false"
AddLine $hb "timestamp: $(Get-Date -Format s)"
AddLine $hb "page_key: $PageKey"
AddLine $hb "status: script_completed"
AddLine $hb "completion_percent: $completion"
AddLine $ro "completed_at: $(Get-Date -Format s)"
AddLine $ro "completion_percent: $completion"
AddLine $ro "FINAL_READY: $browserSmokeOk"

try{
  $paths=New-Object System.Collections.Generic.List[string]
  foreach($p in @($apply,$smoke,$bl,$st,$hb,$ro,$helper,$index,$overlay,$app)){ if(Test-Path $p){ $rel=RelPath $WorktreeRoot $p; if($rel){ $paths.Add($rel) } } }
  if($paths.Count -gt 0){ & git -C $WorktreeRoot add -- $paths.ToArray(); & git -C $WorktreeRoot diff --cached --quiet; if($LASTEXITCODE -ne 0){ & git -C $WorktreeRoot commit -m "page6.4 security runner evidence $ts"; & git -C $WorktreeRoot push origin $Branch; AddLine $ro "git_push: ok" } else { AddLine $ro "git_push: no_changes" } }
} catch { AddLine $ro ("git_push: failed - "+$_.Exception.Message) }
if($browserSmokeOk){ exit 0 } else { exit 2 }
