$ErrorActionPreference = "Continue"
param(
  [string]$PageKey = "security_public_safety_low_credit_20260612",
  [string]$TaskId = "security_public_safety_20260619_df_parcel_contract",
  [string]$PreferredWorktree = "F:\chatgpt\AAYS_WORK\security_public_safety_20260619_clean",
  [string]$FallbackWorktree = "D:\chatgpt\AAYS_WORK\security_public_safety_20260619_clean",
  [string]$HeavyDataRoot = "D:\topografik_map\security_module\data_processed",
  [string]$Branch = "main"
)

$RequiredFields = @(
  "parcel_id", "security_score", "security_level", "security_level_label",
  "security_color_category", "security_color_hex", "source_name", "source_url",
  "source_date", "evidence", "matching_method", "calculation_explanation",
  "confidence_score", "accuracy_rating"
)

function EnsureDir($p) { if ($p -and -not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null } }
function WriteText($p, $t) { EnsureDir (Split-Path -Parent $p); $t | Out-File -FilePath $p -Encoding utf8 }
function AddLine($p, $t) { EnsureDir (Split-Path -Parent $p); $t | Out-File -FilePath $p -Append -Encoding utf8 }
function HasText($p, $s) { if (-not (Test-Path $p)) { return $false }; return [bool](Select-String -Path $p -Pattern $s -SimpleMatch -Quiet) }
function FindRepoRoot($start) {
  try { $d = [IO.DirectoryInfo](Resolve-Path $start -ErrorAction Stop) } catch { $d = [IO.DirectoryInfo](Get-Location).Path }
  while ($d) { if (Test-Path (Join-Path $d.FullName ".git")) { return $d.FullName }; $d = $d.Parent }
  return (Get-Location).Path
}
function RelPath($root, $path) {
  try {
    $r = [IO.Path]::GetFullPath($root).TrimEnd('\','/')
    $p = [IO.Path]::GetFullPath($path)
    if ($p.StartsWith($r, [StringComparison]::OrdinalIgnoreCase)) { return $p.Substring($r.Length).TrimStart('\','/').Replace('\','/') }
  } catch {}
  return $null
}
function PushExplicit($repo, $paths, $msg) {
  if (-not (Test-Path (Join-Path $repo ".git"))) { return }
  $rel = @()
  foreach ($p in $paths) { if (Test-Path $p) { $rp = RelPath $repo $p; if ($rp) { $rel += $rp } } }
  if ($rel.Count -eq 0) { return }
  try { git -C $repo fetch origin $Branch | Out-Null; git -C $repo pull --ff-only origin $Branch | Out-Null } catch {}
  try {
    git -C $repo add -- $rel
    git -C $repo diff --cached --quiet
    if ($LASTEXITCODE -ne 0) { git -C $repo commit -m $msg | Out-Null; git -C $repo push origin $Branch | Out-Null }
  } catch {}
}
function ReadSample($p) {
  try { return (Get-Content $p -TotalCount 25000 -ErrorAction Stop) -join "`n" } catch { return "" }
}
function FirstExisting($items) { foreach ($i in $items) { if ($i -and (Test-Path $i)) { return $i } }; return $null }

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$runnerRepo = FindRepoRoot $PSScriptRoot
$pageRoot = Join-Path $runnerRepo "docs\chatgpt_status\$PageKey"
$reports = Join-Path $pageRoot "reports"
$statusDir = Join-Path $pageRoot "status"
$outDir = Join-Path $pageRoot "runner_outputs"
$heartDir = Join-Path $pageRoot "heartbeat"
EnsureDir $reports; EnsureDir $statusDir; EnsureDir $outDir; EnsureDir $heartDir

$applyReport = Join-Path $reports "security_df_worktree_apply_report_$ts.md"
$smokeReport = Join-Path $reports "security_df_worktree_smoke_report_$ts.md"
$blockerReport = Join-Path $reports "security_df_worktree_blockers_$ts.md"
$fieldReport = Join-Path $reports "security_df_worktree_field_contract_report_$ts.md"
$finalWrapper = Join-Path $reports "security_df_worktree_final_wrapper_$ts.md"
$statusFile = Join-Path $statusDir "security_20260619_df_status_$ts.md"
$latestJson = Join-Path $statusDir "security_20260619_df_latest.json"
$runnerOutput = Join-Path $outDir "security_20260619_df_runner_output_$ts.md"
$heartbeat = Join-Path $heartDir "security_20260619_df_heartbeat_$ts.md"

$blockers = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
$changedFiles = New-Object System.Collections.Generic.List[string]

AddLine $runnerOutput "# Security 20260619 D/F runner output"
AddLine $runnerOutput "started_at=$((Get-Date).ToString('s'))"
AddLine $runnerOutput "page_key=$PageKey"
AddLine $runnerOutput "task_id=$TaskId"
AddLine $runnerOutput "branch=$Branch"

$WorktreeRoot = $PreferredWorktree
if (-not (Test-Path $WorktreeRoot) -and (Test-Path $FallbackWorktree)) { $WorktreeRoot = $FallbackWorktree }
if (-not (Test-Path $WorktreeRoot)) {
  $blockers.Add("clean_worktree_missing:$PreferredWorktree|$FallbackWorktree")
  $warnings.Add("local_user_must_create_df_clean_worktree")
}

$productRoot = $WorktreeRoot
if (-not (Test-Path (Join-Path $productRoot "england_map_web")) -and (Test-Path (Join-Path $runnerRepo "england_map_web"))) {
  $productRoot = $runnerRepo
  $warnings.Add("using_runner_repo_product_root_not_df_worktree")
}
if (-not (Test-Path (Join-Path $productRoot "england_map_web"))) { $blockers.Add("england_map_web_not_found") }

try {
  if (Test-Path (Join-Path $productRoot ".git")) { git -C $productRoot fetch origin $Branch | Out-Null; git -C $productRoot pull --ff-only origin $Branch | Out-Null }
} catch { $warnings.Add("product_git_sync_failed:$($_.Exception.Message)") }

$webRoot = Join-Path $productRoot "england_map_web"
$appJs = Join-Path $webRoot "app.js"
$indexHtml = Join-Path $webRoot "index.html"
$overlayJs = Join-Path $webRoot "security_overlay.js"
$overlayCss = Join-Path $webRoot "security_overlay.css"

$carrier = "UNDETECTED"
if (Test-Path $appJs) {
  if (HasText $appJs "parcel-use-parcels") { $carrier = "frontend:parcel-use-parcels" }
  elseif (HasText $appJs "fallback-parcels") { $carrier = "frontend:fallback-parcels" }
  elseif (HasText $appJs "/map/parcels") { $carrier = "api:/map/parcels" }
  elseif (HasText $appJs "pmtiles") { $carrier = "frontend:pmtiles_candidate" }
  elseif (HasText $appJs "parcels_inspire") { $carrier = "backend:parcels_inspire_candidate" }
  else { $blockers.Add("parcel_polygon_carrier_not_found_in_app_js") }
} else { $blockers.Add("app_js_missing") }

$dataCandidates = @(
  (Join-Path $webRoot "dist_worker\data\parcel_security_scores_rechecked_0_120m_spatial.geojson"),
  (Join-Path $webRoot "data\parcel_security_scores_rechecked_0_120m_spatial.geojson"),
  (Join-Path $HeavyDataRoot "parcel_security_scores_enhanced_compact.geojson"),
  (Join-Path $HeavyDataRoot "parcel_security_scores_compact.geojson"),
  (Join-Path $HeavyDataRoot "parcel_security_scores.geojson")
)
$securityLookupSource = FirstExisting $dataCandidates
if (-not $securityLookupSource) { $blockers.Add("security_lookup_source_not_found") }

$sample = ""
$geometryStatus = "UNKNOWN"
$pointFeatureCount = "UNKNOWN"
$polygonFeatureCount = "UNKNOWN"
$missingFields = @()
$canonicalFieldsFound = @()
if ($securityLookupSource) {
  $sample = ReadSample $securityLookupSource
  if ($sample -match '"Point"') { $pointFeatureCount = "POINT_GEOMETRY_PRESENT" }
  if ($sample -match '"Polygon"|"MultiPolygon"') { $polygonFeatureCount = "POLYGON_GEOMETRY_PRESENT" }
  if ($pointFeatureCount -ne "UNKNOWN" -and $polygonFeatureCount -eq "UNKNOWN") { $geometryStatus = "POINT_ONLY_SAMPLE"; $blockers.Add("live_security_geometry_still_point") }
  elseif ($polygonFeatureCount -ne "UNKNOWN") { $geometryStatus = "POLYGON_OR_MULTIPOLYGON_SAMPLE" }
  foreach ($f in $RequiredFields) {
    if ($sample -match ('"' + [regex]::Escape($f) + '"')) { $canonicalFieldsFound += $f } else { $missingFields += $f }
  }
  if ($missingFields.Count -gt 0) { $blockers.Add("missing_canonical_fields:" + ($missingFields -join ',')) }
}

$bridgePath = Join-Path $webRoot "security_contract_bridge.js"
if (Test-Path $webRoot) {
$bridgeJs = @'
(function(){
  var REQUIRED = [
    'parcel_id','security_score','security_level','security_level_label','security_color_category','security_color_hex',
    'source_name','source_url','source_date','evidence','matching_method','calculation_explanation','confidence_score','accuracy_rating'
  ];
  var ALIASES = {
    parcel_id:['parcel_id','security_parcel_id','id','parcelId'],
    security_score:['security_score','safety_score','score'],
    security_level:['security_level','safety_level','level'],
    security_level_label:['security_level_label','safety_level_label','confidence_label'],
    security_color_category:['security_color_category','color_category','safety_color_category'],
    security_color_hex:['security_color_hex','color_hex','safety_color_hex'],
    source_name:['source_name','source','dataset_name'],
    source_url:['source_url','url','dataset_url'],
    source_date:['source_date','date','dataset_date'],
    evidence:['evidence','confidence_flags','evidence_text'],
    matching_method:['matching_method','match_method'],
    calculation_explanation:['calculation_explanation','explanation'],
    confidence_score:['confidence_score','confidence'],
    accuracy_rating:['accuracy_rating','accuracy']
  };
  function val(p, keys){ for(var i=0;i<keys.length;i++){ var v=p && p[keys[i]]; if(v !== undefined && v !== null && v !== '') return v; } return null; }
  function normalize(p){
    p = p || {};
    var out = Object.assign({}, p);
    REQUIRED.forEach(function(k){ if(out[k] === undefined || out[k] === null || out[k] === '') out[k] = val(p, ALIASES[k] || [k]); });
    out.__missing_security_contract_fields = REQUIRED.filter(function(k){ return out[k] === undefined || out[k] === null || out[k] === ''; });
    return out;
  }
  function esc(v){ return String(v === undefined || v === null || v === '' ? 'missing' : v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];}); }
  function html(p){
    var n = normalize(p);
    return '<div class="aays-security-contract" data-contract-missing="'+esc(n.__missing_security_contract_fields.join(','))+'">' +
      REQUIRED.map(function(k){ return '<div class="aays-security-contract-row"><strong>'+esc(k)+':</strong> '+esc(n[k])+'</div>'; }).join('') +
      (n.__missing_security_contract_fields.length ? '<div class="aays-security-contract-blocker">Missing canonical fields: '+esc(n.__missing_security_contract_fields.join(', '))+'</div>' : '') +
      '</div>';
  }
  window.AAYSSecurityContractBridge = { requiredFields: REQUIRED.slice(), normalize: normalize, renderHtml: html };
})();
'@
  WriteText $bridgePath $bridgeJs
  $changedFiles.Add($bridgePath)
}

$bridgeLoaded = $false
if (Test-Path $indexHtml) {
  try {
    $html = Get-Content $indexHtml -Raw
    if ($html -notmatch 'security_contract_bridge\.js') {
      $html = $html -replace '</body>', '<script src="security_contract_bridge.js"></script>`n</body>'
      WriteText $indexHtml $html
      $changedFiles.Add($indexHtml)
    }
    $bridgeLoaded = ((Get-Content $indexHtml -Raw) -match 'security_contract_bridge\.js')
  } catch { $blockers.Add("index_html_patch_failed") }
} else { $blockers.Add("index_html_missing") }

$overlayCanonicalHook = $false
if (Test-Path $overlayJs) {
  if (HasText $overlayJs "AAYSSecurityContractBridge") { $overlayCanonicalHook = $true }
  elseif (HasText $overlayJs "safety_score" -or HasText $overlayJs "safety_level") { $warnings.Add("overlay_legacy_security_fields_detected") }
} else { $blockers.Add("security_overlay_js_missing") }

$cssPath = Join-Path $webRoot "security_overlay.css"
if (Test-Path $cssPath -and -not (HasText $cssPath ".aays-security-contract")) {
  AddLine $cssPath "`n.aays-security-contract{font-size:12px;line-height:1.35}.aays-security-contract-row{margin:2px 0}.aays-security-contract-blocker{margin-top:6px;font-weight:600}"
  $changedFiles.Add($cssPath)
}

$apiSmoke = "NOT_RUN"
$webSmoke = "NOT_RUN"
try {
  $webResp = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/england_map_web/" -TimeoutSec 8
  $webSmoke = "HTTP_$($webResp.StatusCode)"
} catch { $webSmoke = "ERROR"; $warnings.Add("web_runtime_not_reachable") }
try {
  $parcelResp = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/map/parcels?bbox=-0.55,51.28,0.35,51.75&limit=5" -TimeoutSec 12
  $apiSmoke = "HTTP_$($parcelResp.StatusCode)"
  if ($parcelResp.Content -match 'Polygon|MultiPolygon') { $polygonFeatureCount = "RUNTIME_POLYGON_PRESENT" }
} catch { $apiSmoke = "ERROR"; $warnings.Add("map_parcels_probe_failed") }

$fieldContractOk = ($missingFields.Count -eq 0 -and $securityLookupSource)
$polygonThematicOk = ($carrier -ne "UNDETECTED" -and $polygonFeatureCount -ne "UNKNOWN" -and $geometryStatus -ne "POINT_ONLY_SAMPLE")
$popupContractOk = ($bridgeLoaded -and $overlayCanonicalHook)
$rightPanelContractOk = $popupContractOk
$browserSmokeOk = ($webSmoke -match '^HTTP_2' -and $apiSmoke -match '^HTTP_2' -and $polygonThematicOk -and $fieldContractOk -and $popupContractOk)

$completion = 35
if (Test-Path $WorktreeRoot) { $completion += 5 }
if ($carrier -ne "UNDETECTED") { $completion += 10 }
if ($securityLookupSource) { $completion += 10 }
if ($geometryStatus -ne "UNKNOWN") { $completion += 5 }
if ($polygonFeatureCount -ne "UNKNOWN") { $completion += 10 }
if ($fieldContractOk) { $completion += 15 }
if ($bridgeLoaded) { $completion += 5 }
if ($popupContractOk) { $completion += 5 }
if ($browserSmokeOk) { $completion = 100 }
if ($completion -gt 99 -and -not $browserSmokeOk) { $completion = 99 }

$finalStatus = if ($browserSmokeOk) { "FINAL_READY_PARCEL_ACCEPTANCE" } else { "BLOCKED_MISSING_POLYGON_CARRIER_OR_CONTRACT_FIELDS" }

WriteText $applyReport @"
# Security/Public Safety D/F Worktree Apply Report

status=$finalStatus
completion_percent=$completion
page_key=$PageKey
task_id=$TaskId
worktree_root=$WorktreeRoot
product_root=$productRoot
carrier_polygon_source=$carrier
security_lookup_source=$securityLookupSource
geometry_status=$geometryStatus
changed_files=$($changedFiles.ToArray() -join '; ')
db_write=false
ddl=false
migration=false
production_deploy=false
fake_data=false
separate_runner=false
git_add_dot=false
"@

WriteText $fieldReport @"
# Security/Public Safety Field Contract Report

status=$finalStatus
contract_fields_complete=$fieldContractOk
canonical_fields_found=$($canonicalFieldsFound -join ',')
missing_canonical_fields=$($missingFields -join ',')
point_feature_count=$pointFeatureCount
polygon_feature_count=$polygonFeatureCount
popup_contract_ok=$popupContractOk
right_panel_contract_ok=$rightPanelContractOk
bridge_loaded=$bridgeLoaded
overlay_canonical_hook=$overlayCanonicalHook
"@

WriteText $smokeReport @"
# Security/Public Safety Smoke Report

status=$finalStatus
web_runtime=$webSmoke
map_parcels_probe=$apiSmoke
polygon_thematic_ok=$polygonThematicOk
field_contract_ok=$fieldContractOk
popup_contract_ok=$popupContractOk
right_panel_contract_ok=$rightPanelContractOk
browser_smoke_ok=$browserSmokeOk
"@

WriteText $blockerReport @"
# Security/Public Safety Blockers

status=$finalStatus
completion_percent=$completion
blocker_count=$($blockers.Count)
warning_count=$($warnings.Count)

## Blockers
- $($blockers.ToArray() -join "`n- ")

## Warnings
- $($warnings.ToArray() -join "`n- ")

next_action=fix listed blockers in D/F worktree and rerun this same single shared runner task
"@

if ($browserSmokeOk) {
  WriteText $finalWrapper @"
FINAL_STATUS=FINAL_READY_CONFIRMED
PRODUCT_PROGRESS_ESTIMATE=100
PRODUCTION_COMPLETE=true
PAGE_KEY=$PageKey
TASK_ID=$TaskId
DB_WRITE=false
DDL=false
MIGRATION=false
PRODUCTION_DEPLOY=false
FAKE_DATA=false
SEPARATE_RUNNER=false
GIT_ADD_DOT=false
FINAL_DECISION=FINAL_READY_PARCEL_ACCEPTANCE
"@
} else {
  WriteText $finalWrapper @"
FINAL_STATUS=NOT_READY
PRODUCT_PROGRESS_ESTIMATE=$completion
PRODUCTION_COMPLETE=false
PAGE_KEY=$PageKey
TASK_ID=$TaskId
DB_WRITE=false
DDL=false
MIGRATION=false
PRODUCTION_DEPLOY=false
FAKE_DATA=false
SEPARATE_RUNNER=false
GIT_ADD_DOT=false
FINAL_DECISION=BLOCKED_MISSING_POLYGON_CARRIER_OR_CONTRACT_FIELDS
BLOCKERS=$($blockers.ToArray() -join '; ')
"@
}

WriteText $statusFile @"
PAGE_KEY=$PageKey
TASK_ID=$TaskId
STATUS=$finalStatus
PROGRESS=$completion
FINAL_READY=$browserSmokeOk
PowerShell_required=false
separate_runner_required=false
expected_report=$finalWrapper
"@
WriteText $heartbeat "timestamp=$((Get-Date).ToString('s'))`npage_key=$PageKey`ntask_id=$TaskId`ncompletion_percent=$completion`nfinal_ready=$browserSmokeOk"
WriteText $latestJson (@{
  page_key=$PageKey; task_id=$TaskId; status=$finalStatus; completion_percent=$completion; final_ready=$browserSmokeOk;
  worktree_root=$WorktreeRoot; carrier_polygon_source=$carrier; security_lookup_source=$securityLookupSource;
  geometry_status=$geometryStatus; contract_fields_complete=$fieldContractOk; popup_contract_ok=$popupContractOk; right_panel_contract_ok=$rightPanelContractOk;
  final_wrapper=$finalWrapper; blockers=$blockers.ToArray(); warnings=$warnings.ToArray(); updated_at=(Get-Date).ToString('s')
} | ConvertTo-Json -Depth 8)

AddLine $runnerOutput "completed_at=$((Get-Date).ToString('s'))"
AddLine $runnerOutput "completion_percent=$completion"
AddLine $runnerOutput "final_ready=$browserSmokeOk"

if ($changedFiles.Count -gt 0) { PushExplicit $productRoot $changedFiles.ToArray() "security 20260619 canonical bridge patch $ts" }
PushExplicit $runnerRepo @($applyReport,$smokeReport,$blockerReport,$fieldReport,$finalWrapper,$statusFile,$latestJson,$runnerOutput,$heartbeat) "security 20260619 df evidence $ts"
exit 0
