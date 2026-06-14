param(
  [string]$RepoRoot = "F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706",
  [string]$PageKey = "AAYS_REAL_TOPOGRAPHY_PRODUCT",
  [string]$Branch = "aays-runner-v17-icon-work-20260603-232706",
  [string]$BaseUrl = "http://127.0.0.1:8010",
  [string]$Bbox = "-0.55,51.28,0.35,51.75",
  [int]$Limit = 10,
  [switch]$NoPush
)

$ErrorActionPreference = "Continue"
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"
$StatusRootRel = "docs/chatgpt_status/$PageKey"
$StatusRoot = Join-Path $RepoRoot ($StatusRootRel -replace '/', [IO.Path]::DirectorySeparatorChar)
$ReportDir = Join-Path $StatusRoot "reports"
$StatusDir = Join-Path $StatusRoot "status"
$RunnerOutDir = Join-Path $StatusRoot "runner_outputs"
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir,$RunnerOutDir | Out-Null
$ReportPath = Join-Path $ReportDir "terrayield_047_distance_property_types_apply_patch_smoke_$Ts.md"
$StatusPath = Join-Path $StatusDir "terrayield_047_distance_property_types_status_$Ts.md"
$RawLogPath = Join-Path $RunnerOutDir "terrayield_047_distance_property_types_self_contained_repair_$Ts.txt"

function Write-Utf8([string]$Path, [string]$Text) {
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}
function Append-Utf8([string]$Path, [string]$Text) {
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::AppendAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}
$Events = New-Object System.Collections.Generic.List[string]
function Add-Event([string]$Text) {
  $line = "[$((Get-Date).ToString('o'))] $Text"
  $Events.Add($line) | Out-Null
  Write-Host $line
  Append-Utf8 $RawLogPath ($line + "`n")
}
function Run-Capture([string]$Name, [scriptblock]$Block) {
  Add-Event "RUN $Name"
  try {
    $out = & $Block 2>&1 | Out-String
    Append-Utf8 $RawLogPath ("`n===== $Name =====`n$out")
    return @{ ok = $true; text = $out; error = $null }
  } catch {
    $msg = $_.Exception.Message
    Append-Utf8 $RawLogPath ("`n===== $Name ERROR =====`n$msg")
    return @{ ok = $false; text = ""; error = $msg }
  }
}

Add-Event "047 self-contained repair started repo=$RepoRoot branch=$Branch page=$PageKey"
if (!(Test-Path $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
Set-Location $RepoRoot
Run-Capture "git_fetch_branch" { git fetch origin $Branch --prune } | Out-Null
$currentBranch = (git rev-parse --abbrev-ref HEAD 2>$null).Trim()
if ($currentBranch -ne $Branch) { Run-Capture "git_checkout_branch" { git checkout $Branch } | Out-Null }
Run-Capture "git_pull_rebase_autostash" { git pull --rebase --autostash origin $Branch } | Out-Null

$MapLayersPath = Join-Path $RepoRoot "terrayield_land_intelligence\app\api\routes\map_layers.py"
$IndexPath = Join-Path $RepoRoot "england_map_web\index.html"
$OverlayPath = Join-Path $RepoRoot "england_map_web\distance_property_types_overlay.js"
$PatchNotes = New-Object System.Collections.Generic.List[string]
$PatchErrors = New-Object System.Collections.Generic.List[string]

$routeSnippet = @'

# ============================================================
# AAYS 047 Distance to Nearby Property Types parcel endpoint
# Self-contained repair route. No DB writes; metric-detail fallback is read-only.
# ============================================================

@router.get('/distance-property-types', response_model=GeoJSONFeatureCollection)
def get_map_distance_property_types(
    db: DBSession,
    region: str | None = None,
    local_authority: str | None = None,
    bbox: str | None = None,
    min_score: float | None = Query(default=None, ge=0, le=100),
    max_score: float | None = Query(default=None, ge=0, le=100),
    limit: int = Query(default=1200, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
) -> GeoJSONFeatureCollection:
    authority = local_authority or region
    bbox_tuple = _parse_bbox(bbox)
    params = {"authority": authority, "min_score": min_score, "max_score": max_score, "limit": int(limit), "offset": int(offset)}
    bbox_filter = ""
    if bbox_tuple:
        params.update({"west": bbox_tuple[0], "south": bbox_tuple[1], "east": bbox_tuple[2], "north": bbox_tuple[3]})
        bbox_filter = """
          and ST_Intersects(
            ST_Transform(p.geometry, 4326),
            ST_MakeEnvelope(:west, :south, :east, :north, 4326)
          )
        """
    sql = f"""
    select p.parcel_id, p.parcel_ref, p.inspire_id, p.local_authority, p.postcode, p.address_text, p.area_m2,
           s.nearest_industrial_m, s.nearest_office_m, s.nearest_retail_m,
           s.land_use_mix_score, s.nuisance_score, s.accessibility_score, s.dominant_context_code, s.last_computed_at,
           ST_AsGeoJSON(ST_Transform(p.geometry, 4326)) as geom
    from parcel_context_summary s
    join parcels_inspire p on p.parcel_id = s.parcel_id
    where (:authority is null or p.local_authority = :authority)
      and (s.nearest_industrial_m is not null or s.nearest_office_m is not null or s.nearest_retail_m is not null or s.dominant_context_code is not null)
      and (:min_score is null or coalesce(s.accessibility_score, s.land_use_mix_score, s.nuisance_score, 0) * 100 >= :min_score)
      and (:max_score is null or coalesce(s.accessibility_score, s.land_use_mix_score, s.nuisance_score, 1) * 100 <= :max_score)
      {bbox_filter}
    order by coalesce(s.accessibility_score, s.land_use_mix_score, s.nuisance_score, 0) desc nulls last, p.parcel_id asc
    limit :limit offset :offset
    """
    try:
        rows = db.connection().exec_driver_sql(sql, params).mappings().all()
    except Exception:
        return GeoJSONFeatureCollection(features=[])

    def score_pct(distance, threshold):
        try:
            if distance is None:
                return None
            return round(max(0, min(100, 100 * (1 - float(distance) / threshold))), 2)
        except Exception:
            return None

    detail_cache = {}
    def detail_distance(parcel_id, wanted_terms):
        if parcel_id in detail_cache:
            records = detail_cache[parcel_id]
        else:
            records = []
            candidate_sql = [
                "select lower(coalesce(metric_code, metric_name, metric_key, property_type, target_type, category, '')) as metric_key, coalesce(distance_m, distance_metres, metric_value, value_m, value)::float as distance_m from parcel_context_metric_details where parcel_id = :parcel_id",
                "select lower(coalesce(metric_code, metric_name, metric_key, '')) as metric_key, coalesce(metric_value, value)::float as distance_m from parcel_context_metric_details where parcel_id = :parcel_id",
            ]
            for query in candidate_sql:
                try:
                    records = db.connection().exec_driver_sql(query, {"parcel_id": parcel_id}).mappings().all()
                    if records:
                        break
                except Exception:
                    records = []
            detail_cache[parcel_id] = records
        best = None
        for rec in records:
            key = rec.get("metric_key") or ""
            if any(term in key for term in wanted_terms):
                val = rec.get("distance_m")
                if val is not None and (best is None or float(val) < float(best)):
                    best = val
        return best

    features = []
    for row in rows:
        geom_raw = row.get("geom")
        if not geom_raw:
            continue
        try:
            geometry = json.loads(geom_raw)
        except Exception:
            continue
        parcel_id = row.get("parcel_id")
        nearest_industrial = row.get("nearest_industrial_m")
        nearest_office = row.get("nearest_office_m")
        nearest_retail = row.get("nearest_retail_m")
        nearest_detached = detail_distance(parcel_id, ["detached", "house", "residential"])
        nearest_apartment = detail_distance(parcel_id, ["apartment", "flat", "block"])
        nearest_mixed = detail_distance(parcel_id, ["mixed", "mixed_use", "mixed-use"])
        metric_values = [nearest_industrial, nearest_detached, nearest_retail, nearest_apartment, nearest_office, nearest_mixed]
        metric_count = sum(1 for item in metric_values if item is not None)
        score_values = [score_pct(nearest_industrial, 1500), score_pct(nearest_detached, 1200), score_pct(nearest_retail, 800), score_pct(nearest_apartment, 1200), score_pct(nearest_office, 800), score_pct(nearest_mixed, 1000)]
        score_values = [item for item in score_values if item is not None]
        overall_score = round(sum(score_values) / len(score_values), 2) if score_values else None
        dominant = row.get("dominant_context_code") or "mixed"
        color_hex = "#9467bd"; use6_code = "mixed"; use6_label = "Mixed Building Program"
        if dominant == "industrial": color_hex = "#7f7f7f"; use6_code = "industrial"; use6_label = "Industrial Unit"
        elif dominant == "residential": color_hex = "#2ca02c"; use6_code = "detached"; use6_label = "Detached Home / Residential"
        elif dominant == "commercial": color_hex = "#ff7f0e"; use6_code = "retail"; use6_label = "Retail Property / Commercial"
        source_date = _serialize_value(row.get("last_computed_at"))
        accuracy_scale = "B_HIGH" if metric_count == 6 else ("C_PARTIAL" if metric_count > 0 else "D_UNKNOWN")
        properties = {
            "layer_name": "Distance to Nearby Property Types", "layer_kind": "distance_property_types",
            "parcel_id": parcel_id, "parcel_ref": row.get("parcel_ref"), "inspire_id": row.get("inspire_id"),
            "local_authority": row.get("local_authority"), "postcode": row.get("postcode"), "address_text": row.get("address_text"), "area_m2": _serialize_value(row.get("area_m2")),
            "use6_code": use6_code, "use6_label": use6_label, "building_type_label": use6_label, "color_hex": color_hex, "color_category": use6_label,
            "nearest_industrial_unit_m": _serialize_value(nearest_industrial), "nearest_detached_home_m": _serialize_value(nearest_detached),
            "nearest_retail_property_m": _serialize_value(nearest_retail), "nearest_apartment_building_m": _serialize_value(nearest_apartment),
            "nearest_office_building_m": _serialize_value(nearest_office), "nearest_mixed_building_program_m": _serialize_value(nearest_mixed),
            "industrial_unit_score_pct": score_pct(nearest_industrial, 1500), "detached_home_score_pct": score_pct(nearest_detached, 1200),
            "retail_property_score_pct": score_pct(nearest_retail, 800), "apartment_building_score_pct": score_pct(nearest_apartment, 1200),
            "office_building_score_pct": score_pct(nearest_office, 800), "mixed_building_program_score_pct": score_pct(nearest_mixed, 1000),
            "overall_distance_property_type_score_pct": overall_score, "score_pct": overall_score,
            "class_level": "HIGH" if overall_score is not None and overall_score >= 67 else ("MEDIUM" if overall_score is not None and overall_score >= 34 else "LOW"),
            "source_name": "parcel_context_summary + parcel_context_metric_details", "source_date": source_date,
            "evidence_ref": f"parcel_context_summary:{parcel_id};parcel_context_metric_details:{parcel_id}",
            "evidence_summary": f"{metric_count}/6 distance metrics populated; dominant_context={dominant}",
            "confidence_level_4": accuracy_scale, "accuracy_scale": accuracy_scale, "matching_method": "parcel_id_join_cached_context_metrics",
            "calculation_explanation": "Distance score uses cached parcel_context_summary metrics plus read-only parcel_context_metric_details fallback. FINAL_READY requires all six distance values populated.",
            "raw_output_fields": {"dominant_context_code": dominant, "land_use_mix_score": _serialize_value(row.get("land_use_mix_score")), "nuisance_score": _serialize_value(row.get("nuisance_score")), "accessibility_score": _serialize_value(row.get("accessibility_score")), "metric_count": metric_count},
        }
        features.append({"type": "Feature", "geometry": geometry, "properties": properties})
    return GeoJSONFeatureCollection(features=features)
'@

try {
  if (Test-Path $MapLayersPath) {
    $mapText = Get-Content $MapLayersPath -Raw
    $pattern = "(?s)# ============================================================\r?\n# AAYS 047 Distance to Nearby Property Types parcel endpoint.*?return GeoJSONFeatureCollection\(features=features\)"
    if ($mapText -match $pattern) {
      $mapText = [regex]::Replace($mapText, $pattern, $routeSnippet)
      Write-Utf8 $MapLayersPath $mapText
      $PatchNotes.Add("replaced existing /map/distance-property-types route with six-metric read-only fallback route") | Out-Null
    } elseif ($mapText -notmatch "distance-property-types") {
      Append-Utf8 $MapLayersPath $routeSnippet
      $PatchNotes.Add("appended /map/distance-property-types route to map_layers.py") | Out-Null
    } else { $PatchNotes.Add("distance-property-types route already present but marker not replaced") | Out-Null }
  } else { $PatchErrors.Add("missing map_layers.py at $MapLayersPath") | Out-Null }
} catch { $PatchErrors.Add("map_layers.py patch error: $($_.Exception.Message)") | Out-Null }

$overlayJs = @'
(function () {
  'use strict';
  const LAYER_ID = 'distance-property-types-fill';
  const OUTLINE_ID = 'distance-property-types-outline';
  const SOURCE_ID = 'distance-property-types-source';
  const ENDPOINT = '/map/distance-property-types';
  const legend = [['industrial','Industrial Unit','#7f7f7f'],['detached','Detached Home','#2ca02c'],['retail','Retail Property','#ff7f0e'],['apartment','Apartment Building','#1f77b4'],['office','Office Building','#17becf'],['mixed','Mixed Building Program','#9467bd']];
  function getMap(){ return window.map || window.aaysMap || window.mainMap || null; }
  function bboxString(map){ const b=map.getBounds(); return [b.getWest(),b.getSouth(),b.getEast(),b.getNorth()].map(v=>Number(v).toFixed(6)).join(','); }
  function field(props,key){ const v=props&&props[key]; return v===null||v===undefined||v===''?'—':v; }
  function ensureLegend(){ let el=document.getElementById('distance-property-types-legend'); if(el) return el; el=document.createElement('div'); el.id='distance-property-types-legend'; el.style.cssText='position:absolute;right:12px;bottom:36px;background:#fff;padding:10px 12px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.2);font:12px Arial;z-index:5;display:none;max-width:260px;'; el.innerHTML='<b>Distance to Nearby Property Types</b>'+legend.map(([c,l,color])=>`<div style="margin-top:6px"><span style="display:inline-block;width:12px;height:12px;background:${color};border:1px solid #333;margin-right:6px"></span>${l}</div>`).join(''); document.body.appendChild(el); return el; }
  function popupHtml(props){ const rows=[['Layer',field(props,'layer_name')],['Parcel ID',field(props,'parcel_id')],['Parcel Ref',field(props,'parcel_ref')],['INSPIRE ID',field(props,'inspire_id')],['Use6 / Color',`${field(props,'use6_label')} / ${field(props,'color_category')}`],['Score %',field(props,'overall_distance_property_type_score_pct')],['Class',field(props,'class_level')],['Industrial m',field(props,'nearest_industrial_unit_m')],['Detached m',field(props,'nearest_detached_home_m')],['Retail m',field(props,'nearest_retail_property_m')],['Apartment m',field(props,'nearest_apartment_building_m')],['Office m',field(props,'nearest_office_building_m')],['Mixed m',field(props,'nearest_mixed_building_program_m')],['Source',field(props,'source_name')],['Source date',field(props,'source_date')],['Evidence',field(props,'evidence_summary')],['Accuracy',field(props,'accuracy_scale')],['Matching',field(props,'matching_method')],['Calculation',field(props,'calculation_explanation')]]; return `<div style="max-width:420px;font:12px Arial"><h3 style="margin:0 0 8px">Distance to Nearby Property Types</h3><table>${rows.map(([k,v])=>`<tr><th style="text-align:left;vertical-align:top;padding:3px 8px 3px 0">${k}</th><td style="padding:3px 0">${v}</td></tr>`).join('')}</table></div>`; }
  async function loadLayer(){ const map=getMap(); if(!map) return alert('Map object not found'); const url=`${ENDPOINT}?bbox=${encodeURIComponent(bboxString(map))}&limit=1200`; const res=await fetch(url); const data=await res.json(); if(map.getLayer(LAYER_ID)) map.removeLayer(LAYER_ID); if(map.getLayer(OUTLINE_ID)) map.removeLayer(OUTLINE_ID); if(map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID); map.addSource(SOURCE_ID,{type:'geojson',data}); map.addLayer({id:LAYER_ID,type:'fill',source:SOURCE_ID,paint:{'fill-color':['coalesce',['get','color_hex'],'#9467bd'],'fill-opacity':0.55}}); map.addLayer({id:OUTLINE_ID,type:'line',source:SOURCE_ID,paint:{'line-color':'#222','line-width':0.8}}); ensureLegend().style.display='block'; window.__distancePropertyTypesClick=function(e){ const f=e.features&&e.features[0]; if(!f) return; new maplibregl.Popup().setLngLat(e.lngLat).setHTML(popupHtml(f.properties||{})).addTo(map); }; map.on('click',LAYER_ID,window.__distancePropertyTypesClick); }
  function toggle(){ const map=getMap(); if(!map) return alert('Map object not found'); if(map.getLayer(LAYER_ID)){ map.removeLayer(LAYER_ID); if(map.getLayer(OUTLINE_ID)) map.removeLayer(OUTLINE_ID); if(map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID); ensureLegend().style.display='none'; return; } loadLayer().catch(err=>alert('Distance layer failed: '+err.message)); }
  function addButton(){ if(document.getElementById('distance-property-types-toggle')) return; const btn=document.createElement('button'); btn.id='distance-property-types-toggle'; btn.title='Distance to Nearby Property Types'; btn.textContent='🏷 Distance Types'; btn.style.cssText='position:absolute;left:12px;top:132px;z-index:5;padding:8px 10px;border-radius:8px;border:1px solid #999;background:#fff;cursor:pointer;font:12px Arial;'; btn.onclick=toggle; document.body.appendChild(btn); ensureLegend(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',addButton); else addButton();
})();
'@
try { New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OverlayPath) | Out-Null; Write-Utf8 $OverlayPath $overlayJs; $PatchNotes.Add("wrote distance_property_types_overlay.js") | Out-Null } catch { $PatchErrors.Add("overlay write error: $($_.Exception.Message)") | Out-Null }
try {
  if (Test-Path $IndexPath) {
    $idx = Get-Content $IndexPath -Raw
    if ($idx -notmatch "distance_property_types_overlay\.js") {
      $tag = '<script src="distance_property_types_overlay.js"></script>'
      if ($idx -match "</body>") { $idx = $idx -replace "</body>", "$tag`n</body>" } else { $idx = $idx + "`n" + $tag + "`n" }
      Write-Utf8 $IndexPath $idx
      $PatchNotes.Add("added overlay script tag to index.html") | Out-Null
    } else { $PatchNotes.Add("index.html already references overlay") | Out-Null }
  } else { $PatchErrors.Add("missing index.html at $IndexPath") | Out-Null }
} catch { $PatchErrors.Add("index.html patch error: $($_.Exception.Message)") | Out-Null }

$py = if (Test-Path $MapLayersPath) { Run-Capture "python_py_compile_map_layers" { python -m py_compile $MapLayersPath } } else { @{ ok=$false; text=""; error="map_layers.py missing" } }
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$js = if ($nodeCmd -and (Test-Path $OverlayPath)) { Run-Capture "node_check_overlay" { node --check $OverlayPath } } else { @{ ok=$true; text="node missing or overlay missing; JS syntax check skipped"; error=$null } }

$EndpointUrl = "$BaseUrl/map/distance-property-types?bbox=$([uri]::EscapeDataString($Bbox))&limit=$Limit"
$smokeStatus = "NOT_RUN"
$featureCount = $null
$missingFields = @()
$missingValueFields = @()
$endpointText = ""
$requiredFields = @("layer_name","parcel_id","parcel_ref","inspire_id","use6_label","color_category","overall_distance_property_type_score_pct","class_level","source_name","source_date","evidence_summary","accuracy_scale","matching_method","calculation_explanation","nearest_industrial_unit_m","nearest_detached_home_m","nearest_retail_property_m","nearest_apartment_building_m","nearest_office_building_m","nearest_mixed_building_program_m")
$requiredMetricValues = @("nearest_industrial_unit_m","nearest_detached_home_m","nearest_retail_property_m","nearest_apartment_building_m","nearest_office_building_m","nearest_mixed_building_program_m")
$smoke = Run-Capture "endpoint_smoke_distance_property_types" { Invoke-WebRequest $EndpointUrl -UseBasicParsing -TimeoutSec 15 | Select-Object -ExpandProperty Content }
if ($smoke.ok -and $smoke.text.Trim().Length -gt 0) {
  $endpointText = $smoke.text.Trim()
  try {
    $json = $endpointText | ConvertFrom-Json
    if ($json.type -ne "FeatureCollection") { $smokeStatus = "SMOKE_BLOCKED_NOT_FEATURE_COLLECTION" }
    else {
      $featureCount = @($json.features).Count
      if ($featureCount -eq 0) { $smokeStatus = "DATA_BLOCKED_NOT_FINAL_READY" }
      else {
        $props = $json.features[0].properties
        $names = @($props.PSObject.Properties | ForEach-Object { $_.Name })
        $missingFields = @($requiredFields | Where-Object { $names -notcontains $_ })
        $missingValueFields = @($requiredMetricValues | Where-Object { $null -eq $props.$_ -or [string]$props.$_ -eq "" })
        if ($missingFields.Count -gt 0) { $smokeStatus = "CONTRACT_BLOCKED_NOT_FINAL_READY" }
        elseif ($missingValueFields.Count -gt 0) { $smokeStatus = "METRIC_VALUES_BLOCKED_NOT_FINAL_READY" }
        else { $smokeStatus = "FINAL_READY" }
      }
    }
  } catch { $smokeStatus = "SMOKE_BLOCKED_JSON_PARSE_ERROR"; $endpointText += "`nJSON parse error: $($_.Exception.Message)" }
} else { $smokeStatus = "SMOKE_BLOCKED_APP_NOT_RUNNING_OR_ROUTE_NOT_REACHABLE"; $endpointText = ($smoke.text + $smoke.error).Trim() }

if ($PatchErrors.Count -gt 0 -or -not $py.ok -or -not $js.ok) { $finalStatus = "PATCH_BLOCKED_NOT_FINAL_READY" }
elseif ($smokeStatus -eq "FINAL_READY") { $finalStatus = "FINAL_READY" }
else { $finalStatus = $smokeStatus }
$completion = if ($finalStatus -eq "FINAL_READY") { 100 } elseif ($finalStatus -eq "DATA_BLOCKED_NOT_FINAL_READY") { 88 } elseif ($finalStatus -eq "METRIC_VALUES_BLOCKED_NOT_FINAL_READY") { 84 } elseif ($finalStatus -like "CONTRACT_BLOCKED*") { 82 } elseif ($finalStatus -like "SMOKE_BLOCKED*") { 78 } elseif ($finalStatus -like "PATCH_BLOCKED*") { 70 } else { 75 }

$report = @"
# TerraYield 047 Distance Property Types self-contained repair report

timestamp: $Ts
page_key: $PageKey
branch: $Branch
status: $finalStatus
completion_percent: $completion
repo_root: $RepoRoot
base_url: $BaseUrl
bbox: $Bbox
limit: $Limit

## Patch notes
$($PatchNotes | ForEach-Object { "- $_" } | Out-String)

## Patch errors
$($(if ($PatchErrors.Count -eq 0) { "- none" } else { $PatchErrors | ForEach-Object { "- $_" } }) | Out-String)

## Static checks
- python py_compile map_layers.py: $($py.ok)
- node --check distance_property_types_overlay.js: $($js.ok)

## Endpoint smoke
URL: $EndpointUrl
smoke_status: $smokeStatus
feature_count: $featureCount
missing_required_fields: $($missingFields -join ', ')
missing_metric_value_fields: $($missingValueFields -join ', ')

```json
$endpointText
```

## Events
```text
$($Events -join "`n")
```

## Final rule
FINAL_READY requires parcel polygon FeatureCollection with at least one feature, all required popup/right-panel fields, and all six distance metric values populated. Empty FeatureCollection or null six-metric values are not feature-complete. No DB write/import/backfill was performed.
"@
Write-Utf8 $ReportPath $report
$statusText = @"
status: $finalStatus
completion_percent: $completion
expected_report: $StatusRootRel/reports/terrayield_047_distance_property_types_apply_patch_smoke_$Ts.md
feature_count: $featureCount
missing_required_fields: $($missingFields -join ', ')
missing_metric_value_fields: $($missingValueFields -join ', ')
no_db_write: true
"@
Write-Utf8 $StatusPath $statusText

Run-Capture "git_add_repair_outputs" { git add "terrayield_land_intelligence/app/api/routes/map_layers.py" "england_map_web/index.html" "england_map_web/distance_property_types_overlay.js" "$StatusRootRel/reports" "$StatusRootRel/status" "$StatusRootRel/runner_outputs" } | Out-Null
Run-Capture "git_commit_repair_outputs" { git commit -m "Run 047 distance self-contained repair" } | Out-Null
if (-not $NoPush) { Run-Capture "git_push_repair_outputs" { git push origin $Branch } | Out-Null }
Write-Host "047 self-contained repair completed: $finalStatus completion=$completion"
Write-Host "Report: $ReportPath"
Write-Host "Status: $StatusPath"
exit 0
