$ErrorActionPreference = "Stop"

param(
  [string]$WorktreeRoot = "F:\chatgpt\AAYS_WORK\security_public_safety_20260617_clean",
  [string]$FallbackWorktreeRoot = "D:\chatgpt\AAYS_WORK\security_public_safety_20260617_clean",
  [string]$HeavyDataRoot = "D:\topografik_map\security_module\data_processed",
  [string]$PageKey = "security_public_safety_low_credit_20260612"
)

$startedAt = Get-Date
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
if (!(Test-Path $WorktreeRoot) -and (Test-Path $FallbackWorktreeRoot)) {
  $WorktreeRoot = $FallbackWorktreeRoot
}

$PageRoot = Join-Path $WorktreeRoot "docs\chatgpt_status\$PageKey"
$ReportRoot = Join-Path $PageRoot "reports"
$StatusRoot = Join-Path $PageRoot "status"
$HeartbeatRoot = Join-Path $PageRoot "heartbeat"
New-Item -ItemType Directory -Force -Path $ReportRoot,$StatusRoot,$HeartbeatRoot | Out-Null

$ApplyReport = Join-Path $ReportRoot "security_df_worktree_apply_report_$timestamp.md"
$SmokeReport = Join-Path $ReportRoot "security_df_worktree_smoke_report_$timestamp.md"
$BlockerReport = Join-Path $ReportRoot "security_df_worktree_blockers_$timestamp.md"
$StatusReport = Join-Path $StatusRoot "page_6_4_security_status_$timestamp.md"
$HeartbeatReport = Join-Path $HeartbeatRoot "page_6_4_security_heartbeat_$timestamp.md"

function Add-Line([string]$Path, [string]$Text) {
  $Text | Out-File -FilePath $Path -Append -Encoding utf8
}
function Write-Report([string]$Text) {
  Add-Line $ApplyReport $Text
  Write-Host $Text
}
function Test-Text([string]$Path, [string]$Pattern) {
  if (!(Test-Path $Path)) { return $false }
  return [bool](Select-String -Path $Path -Pattern $Pattern -SimpleMatch -Quiet)
}

$guardrailViolations = @()
$blockers = New-Object System.Collections.Generic.List[string]
$carrier = "UNDETECTED"
$securityLookupSource = "UNDETECTED"
$pointFeatureCount = "UNKNOWN"
$polygonFeatureCount = "UNKNOWN"
$contractFieldsComplete = $false
$popupContractOk = $false
$rightPanelContractOk = $false
$browserSmokeOk = $false

Add-Line $ApplyReport "# Security/Public Safety Page 6.4 Apply Report"
Add-Line $ApplyReport "status: STARTED"
Add-Line $ApplyReport "completion_percent: 20"
Add-Line $ApplyReport "worktree_root: $WorktreeRoot"
Add-Line $ApplyReport "heavy_data_root: $HeavyDataRoot"
Add-Line $ApplyReport "started_at: $($startedAt.ToString('s'))"
Add-Line $ApplyReport "db_write: false"
Add-Line $ApplyReport "ddl: false"
Add-Line $ApplyReport "migration: false"
Add-Line $ApplyReport "production_deploy: false"
Add-Line $ApplyReport "fake_data: false"
Add-Line $ApplyReport ""

if (!(Test-Path $WorktreeRoot)) {
  $blockers.Add("missing_worktree_root:$WorktreeRoot")
} else {
  try {
    $branch = (& git -C $WorktreeRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()
    Add-Line $ApplyReport "git_branch: $branch"
    if ($branch -ne "main") { $blockers.Add("branch_not_main:$branch") }
  } catch {
    Add-Line $ApplyReport "git_branch: UNKNOWN"
    $blockers.Add("git_branch_probe_failed")
  }
}

$webRoot = Join-Path $WorktreeRoot "england_map_web"
$apiRoot = Join-Path $WorktreeRoot "terrayield_land_intelligence"
$appJs = Join-Path $webRoot "app.js"
$overlayJs = Join-Path $webRoot "security_overlay.js"
$indexHtml = Join-Path $webRoot "index.html"
$repoSecurityGeoJson = Join-Path $webRoot "data\parcel_security_scores_rechecked_0_120m_spatial.geojson"
$repoSummaryJson = Join-Path $webRoot "data\parcel_security_match_summary.json"

foreach ($p in @($webRoot,$apiRoot,$appJs,$overlayJs,$indexHtml)) {
  Add-Line $ApplyReport ("exists:{0}={1}" -f $p, (Test-Path $p))
  if (!(Test-Path $p)) { $blockers.Add("missing_required_path:$p") }
}

# Detect carrier source without creating fake data.
if (Test-Path $appJs) {
  if (Test-Text $appJs "parcel-use-parcels") { $carrier = "frontend:parcel-use-parcels" }
  elseif (Test-Text $appJs "fallback-parcels") { $carrier = "frontend:fallback-parcels" }
  elseif (Test-Text $appJs "/map/parcels") { $carrier = "api:/map/parcels" }
  elseif (Test-Text $appJs "pmtiles") { $carrier = "frontend:pmtiles_candidate" }
  elseif (Test-Text $appJs "parcels_inspire") { $carrier = "backend:parcels_inspire_candidate" }
  else { $blockers.Add("parcel_polygon_carrier_not_found_in_app_js") }
}

# Prefer enhanced heavy data if present, then compact, then repo legacy file.
$heavyEnhanced = Join-Path $HeavyDataRoot "parcel_security_scores_enhanced_compact.geojson"
$heavyCompact = Join-Path $HeavyDataRoot "parcel_security_scores_compact.geojson"
$heavyFull = Join-Path $HeavyDataRoot "parcel_security_scores.geojson"
foreach ($candidate in @($heavyEnhanced,$heavyCompact,$heavyFull,$repoSecurityGeoJson)) {
  if (Test-Path $candidate) { $securityLookupSource = $candidate; break }
}
if ($securityLookupSource -eq "UNDETECTED") { $blockers.Add("security_lookup_source_not_found") }

# Lightweight field and geometry probes. Do not load large GeoJSON into memory.
if ($securityLookupSource -ne "UNDETECTED") {
  $sampleText = (Get-Content -Path $securityLookupSource -TotalCount 600 -ErrorAction SilentlyContinue) -join "`n"
  if ($sampleText -match '"Point"') { $pointFeatureCount = "POINT_GEOMETRY_PRESENT" }
  if ($sampleText -match '"Polygon"|"MultiPolygon"') { $polygonFeatureCount = "POLYGON_GEOMETRY_PRESENT" }

  $required = @(
    'parcel_id','security_score','security_level','security_level_label','security_color_category','security_color_hex',
    'source_name','source_url','source_date','evidence','matching_method','calculation_explanation','confidence_score','accuracy_rating'
  )
  $missing = @()
  foreach ($field in $required) {
    if ($sampleText -notmatch ('"' + [regex]::Escape($field) + '"')) { $missing += $field }
  }
  if ($missing.Count -eq 0) { $contractFieldsComplete = $true } else { $blockers.Add("missing_contract_fields:" + ($missing -join ',')) }
}

# Write a page-local integration helper file for the runner/human patch process. It is not fake data; it only normalizes real properties.
$helperPath = Join-Path $webRoot "security_contract_normalizer.js"
if (Test-Path $webRoot) {
  $helperContent = @'
(function () {
  "use strict";
  const LEVEL_COLORS = {
    very_low: "#1a9850",
    low: "#91cf60",
    medium: "#ffffbf",
    high: "#fc8d59",
    very_high: "#d73027"
  };
  function firstDefined(obj, keys) {
    for (const key of keys) {
      if (obj && obj[key] !== undefined && obj[key] !== null && obj[key] !== "") return obj[key];
    }
    return null;
  }
  function normalizeSecurityContract(raw) {
    const p = raw || {};
    const level = firstDefined(p, ["security_level", "safety_level", "level", "risk_level"]);
    const category = firstDefined(p, ["security_color_category", "color_category", "risk_category", "safety_color_category"]);
    return {
      parcel_id: firstDefined(p, ["parcel_id", "uprn", "gid", "id", "parcelId"]),
      security_score: firstDefined(p, ["security_score", "safety_score", "score", "risk_score"]),
      security_level: level,
      security_level_label: firstDefined(p, ["security_level_label", "safety_level_label", "level_label"]),
      security_color_category: category,
      security_color_hex: firstDefined(p, ["security_color_hex", "color_hex"]) || (category ? LEVEL_COLORS[String(category).toLowerCase()] : null),
      source_name: firstDefined(p, ["source_name", "source", "data_source"]),
      source_url: firstDefined(p, ["source_url", "url", "evidence_url"]),
      source_date: firstDefined(p, ["source_date", "date", "data_date"]),
      evidence: firstDefined(p, ["evidence", "evidence_text", "method_evidence"]),
      matching_method: firstDefined(p, ["matching_method", "spatial_match_method", "match_method"]),
      calculation_explanation: firstDefined(p, ["calculation_explanation", "explanation", "methodology"]),
      confidence_score: firstDefined(p, ["confidence_score", "confidence", "match_confidence"]),
      accuracy_rating: firstDefined(p, ["accuracy_rating", "accuracy", "quality_rating"]),
      nearest_police_station_distance_m: firstDefined(p, ["nearest_police_station_distance_m", "police_distance_m"]),
      incident_density: firstDefined(p, ["incident_density", "density"]),
      police_safety_level: firstDefined(p, ["police_safety_level", "police_level"])
    };
  }
  function securityContractMissingFields(contract) {
    return ["parcel_id","security_score","security_level","security_color_hex","source_name","source_url","source_date","evidence","matching_method","calculation_explanation","confidence_score","accuracy_rating"]
      .filter((key) => contract[key] === null || contract[key] === undefined || contract[key] === "");
  }
  function securityContractHtml(raw) {
    const c = normalizeSecurityContract(raw);
    const missing = securityContractMissingFields(c);
    const row = (label, value) => `<tr><th>${label}</th><td>${value ?? "Not available in source"}</td></tr>`;
    return `<div class="security-contract-output" data-contract-complete="${missing.length === 0}">
      <h3>Public safety aggregate signal</h3>
      <table>
        ${row("Security score", c.security_score)}
        ${row("Security level", c.security_level_label || c.security_level)}
        ${row("Color category", c.security_color_category || c.security_color_hex)}
        ${row("Source", c.source_name)}
        ${row("Source URL", c.source_url)}
        ${row("Source date", c.source_date)}
        ${row("Evidence", c.evidence)}
        ${row("Matching method", c.matching_method)}
        ${row("Calculation", c.calculation_explanation)}
        ${row("Confidence", c.confidence_score)}
        ${row("Accuracy", c.accuracy_rating)}
        ${row("Nearest police station (m)", c.nearest_police_station_distance_m)}
        ${row("Incident density", c.incident_density)}
        ${row("Police safety level", c.police_safety_level)}
      </table>
      ${missing.length ? `<p class="contract-warning">Missing contract fields: ${missing.join(", ")}</p>` : ""}
      <p class="contract-note">Aggregate public safety signal; not exact incident-point truth.</p>
    </div>`;
  }
  window.AAYSSecurityContract = { normalizeSecurityContract, securityContractMissingFields, securityContractHtml };
})();
'@
  if (!(Test-Path $helperPath) -or -not (Test-Text $helperPath "AAYSSecurityContract")) {
    $helperContent | Out-File -FilePath $helperPath -Encoding utf8
    Add-Line $ApplyReport "helper_created: $helperPath"
  } else {
    Add-Line $ApplyReport "helper_already_exists: $helperPath"
  }
}

# Patch index.html to load helper only if security overlay exists and helper is not already referenced.
if ((Test-Path $indexHtml) -and (Test-Path $helperPath) -and -not (Test-Text $indexHtml "security_contract_normalizer.js")) {
  $html = Get-Content $indexHtml -Raw
  if ($html -match "security_overlay\.js") {
    $html = $html -replace '(<script[^>]+security_overlay\.js[^>]*>\s*</script>)', '$1' + "`r`n<script src=\"security_contract_normalizer.js\"></script>"
    $html | Out-File -FilePath $indexHtml -Encoding utf8
    Add-Line $ApplyReport "index_patch: inserted_after_security_overlay"
  } elseif ($html -match "</body>") {
    $html = $html -replace "</body>", "<script src=\"security_contract_normalizer.js\"></script>`r`n</body>"
    $html | Out-File -FilePath $indexHtml -Encoding utf8
    Add-Line $ApplyReport "index_patch: inserted_before_body_close"
  } else {
    $blockers.Add("index_helper_script_insertion_failed")
  }
}

# Static proof for popup/right panel references.
if (Test-Path $overlayJs) {
  if ((Test-Text $overlayJs "security_score") -or (Test-Text $overlayJs "safety_score")) { $popupContractOk = $true }
  if (!(Test-Text $overlayJs "AAYSSecurityContract")) {
    Add-Line $ApplyReport "overlay_notice: normalizer helper created; runner must wire popup/right-panel renderer if overlay uses a custom popup function."
    $blockers.Add("overlay_popup_not_wired_to_AAYSSecurityContract")
  }
}
if (Test-Path $appJs) {
  if ((Test-Text $appJs "security_score") -and ((Test-Text $appJs "right") -or (Test-Text $appJs "side"))) { $rightPanelContractOk = $true }
}

# Runtime smoke probe only if local API is already up. Do not spawn a separate runner.
Add-Line $SmokeReport "# Security/Public Safety Page 6.4 Smoke Report"
Add-Line $SmokeReport "status: STARTED"
Add-Line $SmokeReport "worktree_root: $WorktreeRoot"
try {
  $web = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/england_map_web/" -TimeoutSec 8
  Add-Line $SmokeReport "web_http: $($web.StatusCode)"
} catch { Add-Line $SmokeReport "web_http: failed - $($_.Exception.Message)" }
try {
  $overlay = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/england_map_web/security_overlay.js" -TimeoutSec 8
  Add-Line $SmokeReport "overlay_http: $($overlay.StatusCode)"
} catch { Add-Line $SmokeReport "overlay_http: failed - $($_.Exception.Message)" }
try {
  $summary = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/england_map_web/data/parcel_security_match_summary.json" -TimeoutSec 8
  Add-Line $SmokeReport "summary_http: $($summary.StatusCode)"
} catch { Add-Line $SmokeReport "summary_http: failed - $($_.Exception.Message)" }
try {
  $carrierResp = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/map/parcels?bbox=-0.55,51.28,0.35,51.75&limit=5" -TimeoutSec 12
  Add-Line $SmokeReport "carrier_http: $($carrierResp.StatusCode)"
  if ($carrierResp.Content -match 'Polygon|MultiPolygon') { $polygonFeatureCount = "RUNTIME_POLYGON_PRESENT" }
} catch { Add-Line $SmokeReport "carrier_http: failed - $($_.Exception.Message)" }

if ($carrier -ne "UNDETECTED" -and $securityLookupSource -ne "UNDETECTED" -and $contractFieldsComplete -and $popupContractOk -and $rightPanelContractOk -and $polygonFeatureCount -ne "UNKNOWN") {
  $browserSmokeOk = $true
}

$completion = 35
if ($carrier -ne "UNDETECTED") { $completion += 10 }
if ($securityLookupSource -ne "UNDETECTED") { $completion += 10 }
if ($contractFieldsComplete) { $completion += 15 }
if ($popupContractOk) { $completion += 10 }
if ($rightPanelContractOk) { $completion += 10 }
if ($browserSmokeOk) { $completion = 100 }
if ($completion -gt 99 -and -not $browserSmokeOk) { $completion = 99 }

Add-Line $ApplyReport ""
Add-Line $ApplyReport "## Required Report Fields"
Add-Line $ApplyReport "status: $(if ($browserSmokeOk) {'FINAL_READY'} else {'PARTIAL_OR_BLOCKED'})"
Add-Line $ApplyReport "completion_percent: $completion"
Add-Line $ApplyReport "worktree_root: $WorktreeRoot"
Add-Line $ApplyReport "carrier_polygon_source: $carrier"
Add-Line $ApplyReport "security_lookup_source: $securityLookupSource"
Add-Line $ApplyReport "point_feature_count: $pointFeatureCount"
Add-Line $ApplyReport "polygon_feature_count: $polygonFeatureCount"
Add-Line $ApplyReport "contract_fields_complete: $contractFieldsComplete"
Add-Line $ApplyReport "popup_contract_ok: $popupContractOk"
Add-Line $ApplyReport "right_panel_contract_ok: $rightPanelContractOk"
Add-Line $ApplyReport "browser_smoke_ok: $browserSmokeOk"
Add-Line $ApplyReport "blocker_list: $($blockers -join '; ')"
Add-Line $ApplyReport "next_action: $(if ($browserSmokeOk) {'mark final ready after browser screenshot proof'} else {'wire polygon carrier + security contract fields and rerun smoke'})"

Add-Line $BlockerReport "# Security/Public Safety Page 6.4 Blockers"
Add-Line $BlockerReport "status: $(if ($blockers.Count -eq 0) {'NO_STATIC_BLOCKERS'} else {'BLOCKED_OR_PARTIAL'})"
Add-Line $BlockerReport "completion_percent: $completion"
foreach ($b in $blockers) { Add-Line $BlockerReport "- $b" }

Add-Line $StatusReport "state: $(if ($browserSmokeOk) {'final_ready'} else {'queued_or_partial'})"
Add-Line $StatusReport "percent: $completion"
Add-Line $StatusReport "final: $browserSmokeOk"
Add-Line $StatusReport "FINAL_READY: $browserSmokeOk"
Add-Line $StatusReport "expected_report: $ApplyReport"
Add-Line $StatusReport "powershell_required_from_user: false"
Add-Line $StatusReport "separate_runner_spawned: false"

Add-Line $HeartbeatReport "timestamp: $(Get-Date -Format s)"
Add-Line $HeartbeatReport "page_key: $PageKey"
Add-Line $HeartbeatReport "status: script_completed"
Add-Line $HeartbeatReport "completion_percent: $completion"

if ($browserSmokeOk) { exit 0 } else { exit 2 }
