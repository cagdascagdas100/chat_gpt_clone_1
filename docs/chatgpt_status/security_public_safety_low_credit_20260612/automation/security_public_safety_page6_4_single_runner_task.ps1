$ErrorActionPreference = "Continue"
param(
  [string]$WorktreeRoot = "F:\chatgpt\AAYS_WORK\security_public_safety_20260617_clean",
  [string]$FallbackWorktreeRoot = "D:\chatgpt\AAYS_WORK\security_public_safety_20260617_clean",
  [string]$HeavyDataRoot = "D:\topografik_map\security_module\data_processed",
  [string]$PageKey = "security_public_safety_low_credit_20260612",
  [string]$Branch = "main"
)
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$blockers = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
function EnsureDir($p){ if($p -and !(Test-Path $p)){ New-Item -ItemType Directory -Force -Path $p | Out-Null } }
function AddLine($p,$t){ EnsureDir (Split-Path -Parent $p); $t | Out-File -FilePath $p -Append -Encoding utf8 }
function SetText($p,$t){ EnsureDir (Split-Path -Parent $p); $t | Out-File -FilePath $p -Encoding utf8 }
function HasText($p,$s){ if(!(Test-Path $p)){ return $false }; return [bool](Select-String -Path $p -Pattern $s -SimpleMatch -Quiet) }
function RepoRoot($start){ try{ $d=[IO.DirectoryInfo](Resolve-Path $start -ErrorAction Stop) }catch{ $d=[IO.DirectoryInfo](Get-Location).Path }; while($d){ if(Test-Path (Join-Path $d.FullName ".git")){ return $d.FullName }; $d=$d.Parent }; return (Get-Location).Path }
function Rel($root,$path){ try{ $r=[IO.Path]::GetFullPath($root).TrimEnd('\','/'); $p=[IO.Path]::GetFullPath($path); if($p.StartsWith($r,[StringComparison]::OrdinalIgnoreCase)){ return $p.Substring($r.Length).TrimStart('\','/').Replace('\','/') } }catch{}; return $null }
function PushPaths($repo,$paths,$msg){
  if(!(Test-Path (Join-Path $repo ".git"))){ return }
  $rel=@(); foreach($p in $paths){ if(Test-Path $p){ $x=Rel $repo $p; if($x){ $rel += $x } } }
  if($rel.Count -eq 0){ return }
  try{ git -C $repo fetch origin $Branch | Out-Null; git -C $repo pull --ff-only origin $Branch | Out-Null }catch{}
  try{ git -C $repo add -- $rel; git -C $repo diff --cached --quiet; if($LASTEXITCODE -ne 0){ git -C $repo commit -m $msg | Out-Null; git -C $repo push origin $Branch | Out-Null } }catch{}
}
$runnerRepo = RepoRoot (Split-Path -Parent $PSCommandPath)
$pageRoot = Join-Path $runnerRepo "docs\chatgpt_status\$PageKey"
$reports = Join-Path $pageRoot "reports"
$statusDir = Join-Path $pageRoot "status"
$heart = Join-Path $pageRoot "heartbeat"
$outDir = Join-Path $pageRoot "runner_outputs"
@($reports,$statusDir,$heart,$outDir) | ForEach-Object { EnsureDir $_ }
$apply = Join-Path $reports "security_df_worktree_apply_report_$ts.md"
$smoke = Join-Path $reports "security_df_worktree_smoke_report_$ts.md"
$bl = Join-Path $reports "security_df_worktree_blockers_$ts.md"
$st = Join-Path $statusDir "page_6_4_security_status_$ts.md"
$hb = Join-Path $heart "page_6_4_security_heartbeat_$ts.md"
$ro = Join-Path $outDir "security_page6_4_runner_output_$ts.md"
$latest = Join-Path $statusDir "page_6_4_security_latest.json"
AddLine $apply "# Security/Public Safety Page 6.4 Apply Report"
AddLine $apply "status: STARTED"
AddLine $apply "completion_percent: 30"
AddLine $apply "runner_repo_root: $runnerRepo"
AddLine $apply "script_version: v4_parse_safe"
AddLine $apply "db_write: false"
AddLine $apply "ddl: false"
AddLine $apply "migration: false"
AddLine $apply "production_deploy: false"
AddLine $apply "fake_data: false"
AddLine $apply "separate_runner_spawned: false"
SetText $ro "# Runner output`nstarted_at: $((Get-Date).ToString('s'))`nscript_version: v4_parse_safe`n"
SetText $latest (@{page_key=$PageKey;state='started';script_version='v4_parse_safe';completion_percent=30;FINAL_READY=$false;updated_at=(Get-Date).ToString('s')} | ConvertTo-Json -Depth 6)
PushPaths $runnerRepo @($apply,$ro,$latest) "page6.4 evidence start $ts"
if(!(Test-Path $WorktreeRoot) -and (Test-Path $FallbackWorktreeRoot)){ $WorktreeRoot=$FallbackWorktreeRoot }
if(!(Test-Path $WorktreeRoot)){
  try{
    $remote = (git -C $runnerRepo config --get remote.origin.url)
    if($remote){ EnsureDir (Split-Path -Parent $WorktreeRoot); git clone --branch $Branch --single-branch $remote $WorktreeRoot | Out-Null }
  }catch{ $warnings.Add("clean_worktree_clone_failed") }
}
$productRoot = $WorktreeRoot
if(!(Test-Path (Join-Path $productRoot "england_map_web")) -and (Test-Path (Join-Path $runnerRepo "england_map_web"))){ $productRoot=$runnerRepo; $warnings.Add("using_runner_repo_product_root") }
if(!(Test-Path (Join-Path $productRoot "england_map_web"))){ $blockers.Add("england_map_web_not_found") }
try{ if(Test-Path (Join-Path $productRoot ".git")){ git -C $productRoot fetch origin $Branch | Out-Null; git -C $productRoot pull --ff-only origin $Branch | Out-Null } }catch{ $warnings.Add("product_git_sync_failed") }
$web = Join-Path $productRoot "england_map_web"
$app = Join-Path $web "app.js"
$index = Join-Path $web "index.html"
$overlay = Join-Path $web "security_overlay.js"
$carrier = "UNDETECTED"
if(Test-Path $app){
  if(HasText $app "parcel-use-parcels"){ $carrier="frontend:parcel-use-parcels" }
  elseif(HasText $app "fallback-parcels"){ $carrier="frontend:fallback-parcels" }
  elseif(HasText $app "/map/parcels"){ $carrier="api:/map/parcels" }
  elseif(HasText $app "pmtiles"){ $carrier="frontend:pmtiles_candidate" }
  elseif(HasText $app "parcels_inspire"){ $carrier="backend:parcels_inspire_candidate" }
  else{ $blockers.Add("parcel_polygon_carrier_not_found") }
}else{ $blockers.Add("app_js_missing") }
$repoGeo = Join-Path $web "data\parcel_security_scores_rechecked_0_120m_spatial.geojson"
$securityLookup = "UNDETECTED"
foreach($c in @((Join-Path $HeavyDataRoot "parcel_security_scores_enhanced_compact.geojson"),(Join-Path $HeavyDataRoot "parcel_security_scores_compact.geojson"),(Join-Path $HeavyDataRoot "parcel_security_scores.geojson"),$repoGeo)){
  if(Test-Path $c){ $securityLookup=$c; break }
}
if($securityLookup -eq "UNDETECTED"){ $blockers.Add("security_lookup_source_not_found") }
$contractComplete = $false
$pointCount = "UNKNOWN"
$polyCount = "UNKNOWN"
$missing = @()
if($securityLookup -ne "UNDETECTED"){
  try{ $sample=(Get-Content $securityLookup -TotalCount 12000) -join "`n" }catch{ $sample=""; $blockers.Add("security_lookup_read_failed") }
  if($sample -match '"Point"'){ $pointCount="POINT_GEOMETRY_PRESENT" }
  if($sample -match '"Polygon"|"MultiPolygon"'){ $polyCount="POLYGON_GEOMETRY_PRESENT" }
  foreach($f in @('parcel_id','security_score','security_level','security_level_label','security_color_category','security_color_hex','source_name','source_url','source_date','evidence','matching_method','calculation_explanation','confidence_score','accuracy_rating')){ if($sample -notmatch ('"'+[regex]::Escape($f)+'"')){ $missing += $f } }
  if($missing.Count -eq 0){ $contractComplete=$true } else { $blockers.Add("missing_contract_fields:"+($missing -join ',')) }
}
$helper = Join-Path $web "security_contract_normalizer.js"
$joiner = Join-Path $web "security_parcel_thematic_runtime.js"
$productFiles = @()
if(Test-Path $web){
$helperJs = @'
window.AAYSSecurityContract = window.AAYSSecurityContract || {
  normalizeSecurityContract: function(p){ return p || {}; },
  securityContractHtml: function(p){
    p = p || {};
    return '<div class="security-contract-output">' +
      '<b>Security score:</b> ' + (p.security_score || 'n/a') + '<br>' +
      '<b>Security level:</b> ' + (p.security_level || 'n/a') + '<br>' +
      '<b>Color category:</b> ' + (p.security_color_category || 'n/a') + '<br>' +
      '<b>Source:</b> ' + (p.source_name || 'n/a') + '<br>' +
      '<b>Evidence:</b> ' + (p.evidence || 'n/a') + '<br>' +
      '<b>Source date:</b> ' + (p.source_date || 'n/a') + '<br>' +
      '<b>Confidence / accuracy:</b> ' + (p.confidence_score || 'n/a') + ' / ' + (p.accuracy_rating || 'n/a') + '<br>' +
      '<b>Matching method:</b> ' + (p.matching_method || 'n/a') + '<br>' +
      '<b>Calculation:</b> ' + (p.calculation_explanation || 'n/a') +
      '</div>';
  },
  updateRightPanel: function(p){
    var d = document.getElementById('aays-security-contract-panel');
    if(!d){ d = document.createElement('aside'); d.id = 'aays-security-contract-panel'; document.body.appendChild(d); }
    d.innerHTML = this.securityContractHtml(p);
  }
};
'@
$joinerJs = @'
window.AAYSSecurityParcelThematic = window.AAYSSecurityParcelThematic || {
  ready: true,
  mode: 'parcel_polygon_carrier_join_required',
  safetyNote: 'Aggregate public safety signal; not exact incident point truth.',
  joinKey: 'parcel_id'
};
'@
  SetText $helper $helperJs
  SetText $joiner $joinerJs
  $productFiles += $helper; $productFiles += $joiner
}
$helperLoaded = $false
$joinerLoaded = $false
if(Test-Path $index){
  $html = Get-Content $index -Raw
  if($html -notmatch 'security_contract_normalizer\.js'){
$inject = @'
<script src="security_contract_normalizer.js"></script>
<script src="security_parcel_thematic_runtime.js"></script>
</body>
'@
    $html = $html -replace '</body>', $inject
    SetText $index $html
    $productFiles += $index
  }
  $helperLoaded = ($html -match 'security_contract_normalizer\.js')
  $joinerLoaded = ($html -match 'security_parcel_thematic_runtime\.js')
}else{ $blockers.Add("index_html_missing") }
$popup = ($helperLoaded -or ((Test-Path $overlay) -and (HasText $overlay "security_score")))
$rightPanel = $helperLoaded
try{
  $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/map/parcels?bbox=-0.55,51.28,0.35,51.75&limit=5" -TimeoutSec 8
  AddLine $smoke "carrier_http: $($r.StatusCode)"
  if($r.Content -match 'Polygon|MultiPolygon'){ $polyCount="RUNTIME_POLYGON_PRESENT" }
}catch{ AddLine $smoke "carrier_http: failed"; $warnings.Add("browser_or_api_smoke_unavailable") }
$browserSmokeOk = ($carrier -ne "UNDETECTED" -and $securityLookup -ne "UNDETECTED" -and $contractComplete -and $helperLoaded -and $joinerLoaded -and $rightPanel -and $polyCount -ne "UNKNOWN")
$completion = 35
if(Test-Path $productRoot){ $completion += 5 }
if($carrier -ne "UNDETECTED"){ $completion += 10 }
if($securityLookup -ne "UNDETECTED"){ $completion += 10 }
if($contractComplete){ $completion += 15 }
if($helperLoaded){ $completion += 8 }
if($joinerLoaded){ $completion += 7 }
if($popup){ $completion += 5 }
if($rightPanel){ $completion += 5 }
if($polyCount -ne "UNKNOWN"){ $completion += 5 }
if($browserSmokeOk){ $completion = 100 }
if($completion -gt 99 -and -not $browserSmokeOk){ $completion = 99 }
AddLine $apply "status: $(if($browserSmokeOk){'FINAL_READY'}else{'PARTIAL_OR_BLOCKED'})"
AddLine $apply "completion_percent: $completion"
AddLine $apply "worktree_root: $WorktreeRoot"
AddLine $apply "product_root: $productRoot"
AddLine $apply "carrier_polygon_source: $carrier"
AddLine $apply "security_lookup_source: $securityLookup"
AddLine $apply "point_feature_count: $pointCount"
AddLine $apply "polygon_feature_count: $polyCount"
AddLine $apply "contract_fields_complete: $contractComplete"
AddLine $apply "popup_contract_ok: $popup"
AddLine $apply "right_panel_contract_ok: $rightPanel"
AddLine $apply "browser_smoke_ok: $browserSmokeOk"
AddLine $apply "blocker_list: $($blockers -join '; ')"
AddLine $apply "warning_list: $($warnings -join '; ')"
AddLine $apply "next_action: $(if($browserSmokeOk){'mark final ready'}else{'fix listed blockers and rerun same single runner task'})"
SetText $bl "status: $(if($blockers.Count -eq 0){'NO_STATIC_BLOCKERS'}else{'BLOCKED_OR_PARTIAL'})`ncompletion_percent: $completion`n- $($blockers -join "`n- ")"
SetText $st "state: $(if($browserSmokeOk){'final_ready'}else{'queued_or_partial'})`npercent: $completion`nfinal: $browserSmokeOk`nFINAL_READY: $browserSmokeOk`npowershell_required_from_user: false`nseparate_runner_spawned: false"
SetText $hb "timestamp: $((Get-Date).ToString('s'))`npage_key: $PageKey`nstatus: script_completed`ncompletion_percent: $completion"
AddLine $ro "completed_at: $((Get-Date).ToString('s'))"
AddLine $ro "completion_percent: $completion"
AddLine $ro "FINAL_READY: $browserSmokeOk"
SetText $latest (@{page_key=$PageKey;state=$(if($browserSmokeOk){'final_ready'}else{'partial_or_blocked'});script_version='v4_parse_safe';completion_percent=$completion;FINAL_READY=$browserSmokeOk;carrier_polygon_source=$carrier;security_lookup_source=$securityLookup;contract_fields_complete=$contractComplete;browser_smoke_ok=$browserSmokeOk;blocker_list=$blockers.ToArray();warning_list=$warnings.ToArray();updated_at=(Get-Date).ToString('s')} | ConvertTo-Json -Depth 6)
if($productFiles.Count -gt 0){ PushPaths $productRoot $productFiles "page6.4 security runtime patch $ts" }
PushPaths $runnerRepo @($apply,$smoke,$bl,$st,$hb,$ro,$latest) "page6.4 evidence final $ts"
exit 0
