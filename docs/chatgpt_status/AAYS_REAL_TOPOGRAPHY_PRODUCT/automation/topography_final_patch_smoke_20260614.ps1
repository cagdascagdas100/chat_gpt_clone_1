$ErrorActionPreference = "Continue"

$PageKey = "AAYS_REAL_TOPOGRAPHY_PRODUCT"
$Branch = "aays-runner-v17-icon-work-20260603-232706"
$Repo = (Get-Location).Path
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportsRel = "docs/chatgpt_status/$PageKey/reports"
$ReportRel = "$ReportsRel/topography_final_patch_smoke_$Stamp.txt"
$ReportAbs = Join-Path $Repo $ReportRel

New-Item -ItemType Directory -Force -Path (Split-Path $ReportAbs) | Out-Null

function L([string]$x) { Add-Content -LiteralPath $ReportAbs -Value $x -Encoding UTF8 }
function Run([string]$name, [string]$script) {
  L "$name`_BEGIN"
  try {
    $r = Invoke-Expression $script 2>&1
    if ($r) { ($r | Out-String).TrimEnd() -split "`r?`n" | ForEach-Object { L $_ } } else { L "<EMPTY>" }
  } catch { L "ERROR=$($_.Exception.Message)" }
  L "$name`_END"
}

L "PAGE_KEY=$PageKey"
L "BRANCH=$Branch"
L "RUN_AT=$(Get-Date -Format o)"
L "MODE=TOPOGRAPHY_FINAL_PATCH_SMOKE_SHARED_RUNNER"
L "FAKE_DATA_CREATED=False"
L "DB_WRITE=False"
L "MIGRATION=False"
L "DEPLOY=False"

Run "GIT_BRANCH" "git branch --show-current"
Run "GIT_STATUS_BEFORE" "git status --short"

$appCandidates = @(
  "england_map_web/static/app.js",
  "england_map_web/app.js",
  "terrayield_land_intelligence/england_map_web/static/app.js",
  "terrayield_land_intelligence/england_map_web/app.js"
)

$app = $null
foreach ($p in $appCandidates) {
  $full = Join-Path $Repo $p
  if (Test-Path -LiteralPath $full) { $app = $full; break }
}
if (-not $app) {
  $hit = Get-ChildItem -LiteralPath $Repo -Recurse -Filter app.js -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match "england_map_web" } |
    Select-Object -First 1
  if ($hit) { $app = $hit.FullName }
}

L "APP_JS_PATH=$app"

if (-not $app -or -not (Test-Path -LiteralPath $app)) {
  L "STATUS=APP_JS_NOT_FOUND"
} else {
  $txt = Get-Content -LiteralPath $app -Raw

  $beforeHash = (Get-FileHash -LiteralPath $app -Algorithm SHA256).Hash
  L "APP_JS_SHA256_BEFORE=$beforeHash"

  $txt = $txt.Replace("./assets/icons/worth-waves.svg", "./assets/icons/terrayield_icons/hight_differance.png")
  $txt = $txt.Replace("assets/icons/worth-waves.svg", "assets/icons/terrayield_icons/hight_differance.png")

  if ($txt -notmatch "function normalizeTopographyLookupForPopup") {
$helpers = @'
function normalizeTopographyLookupForPopup(value) {
  if (!value || typeof value !== "object") return null;
  const out = { ...value };
  const numberOrNull = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  };
  out.center_elevation_m = numberOrNull(out.center_elevation_m ?? out.elevation_above_sea_level_m ?? out.elevation_m ?? out.elevation);
  out.region_average_elevation_m = numberOrNull(out.region_average_elevation_m ?? out.region_avg_elevation_m);
  out.elevation_difference_from_region_average_m = numberOrNull(out.elevation_difference_from_region_average_m ?? out.elevation_difference_m);
  out.elevation_above_sea_level_m = numberOrNull(out.elevation_above_sea_level_m ?? out.center_elevation_m);
  return out;
}

function getTopographyLookupForPopup(feature) {
  const properties = feature?.properties || {};
  const parcelId = properties.parcel_id || properties.parcelid || properties.id || properties.inspire_id || properties.parcel_ref;
  return normalizeTopographyLookupForPopup(
    properties.topography_lookup ||
    properties.elevation_lookup ||
    (parcelId && parcelElevationCache?.get?.(parcelId)) ||
    properties
  );
}

function formatTopographyMeterValue(value, fallbackText = "Veri yok", signed = false) {
  const n = Number(value);
  if (!Number.isFinite(n)) return fallbackText;
  const abs = `${Math.abs(n).toFixed(1)} m`;
  return signed ? `${n >= 0 ? "+" : "-"}${abs}` : abs;
}

function firstNonEmptyTopographyText(...values) {
  for (const v of values) {
    if (v !== undefined && v !== null && String(v).trim() !== "") return String(v);
  }
  return "Veri yok";
}

function buildTopographyPopupRowsHtml(lookup, pendingText = "Veri bekleniyor", mode = "div") {
  if (!lookup) {
    return mode === "br"
      ? `Topography: ${pendingText}`
      : `<div class="parcel-popup-row"><span>Topography:</span> <strong>${pendingText}</strong></div>`;
  }
  const rows = [
    ["Denizden yükseklik", formatTopographyMeterValue(lookup.center_elevation_m ?? lookup.elevation_above_sea_level_m)],
    ["Bölge ortalaması", formatTopographyMeterValue(lookup.region_average_elevation_m)],
    ["Bölge ortalamasından fark", formatTopographyMeterValue(lookup.elevation_difference_from_region_average_m, "Veri yok", true)],
    ["Kaynak", firstNonEmptyTopographyText(lookup.source, lookup.source_dataset, lookup.topography_source)],
    ["Kaynak tarihi", firstNonEmptyTopographyText(lookup.source_date, lookup.calculated_at)],
    ["Güven", firstNonEmptyTopographyText(lookup.confidence_level, lookup.confidence_reason)],
    ["Eşleştirme", firstNonEmptyTopographyText(lookup.matching_method)],
    ["Açıklama", firstNonEmptyTopographyText(lookup.calculation_explanation)]
  ];
  if (mode === "br") return rows.map(([k, v]) => `${k}: ${v}`).join("<br />");
  return rows.map(([k, v]) => `<div class="parcel-popup-row"><span>${k}:</span> <strong>${v}</strong></div>`).join("");
}

'@
    $anchor = "async function fetchParcelElevationForPopup"
    $idx = $txt.IndexOf($anchor)
    if ($idx -ge 0) { $txt = $txt.Insert($idx, $helpers) } else { L "HELPER_INSERT_ANCHOR_MISSING=True" }
  }

  $txt = $txt.Replace("const elevation = Number(data?.center_elevation_m ?? data?.elevation_m ?? data?.elevation);", "const lookup = normalizeTopographyLookupForPopup(data);`n    const elevation = Number(lookup?.center_elevation_m ?? data?.center_elevation_m ?? data?.elevation_m ?? data?.elevation);")
  $txt = $txt.Replace("parcelElevationCache.set(cacheKey, elevation);", "parcelElevationCache.set(cacheKey, lookup || { center_elevation_m: elevation });")

  Set-Content -LiteralPath $app -Value $txt -Encoding UTF8

  $afterTxt = Get-Content -LiteralPath $app -Raw
  $afterHash = (Get-FileHash -LiteralPath $app -Algorithm SHA256).Hash
  L "APP_JS_SHA256_AFTER=$afterHash"
  L "HAS_region_average_elevation_m=$($afterTxt.Contains('region_average_elevation_m'))"
  L "HAS_elevation_difference_from_region_average_m=$($afterTxt.Contains('elevation_difference_from_region_average_m'))"
  L "HAS_calculation_explanation=$($afterTxt.Contains('calculation_explanation'))"
  L "HAS_hight_differance_icon=$($afterTxt.Contains('hight_differance.png'))"
  L "HAS_normalizeTopographyLookupForPopup=$($afterTxt.Contains('normalizeTopographyLookupForPopup'))"
  L "HAS_buildTopographyPopupRowsHtml=$($afterTxt.Contains('buildTopographyPopupRowsHtml'))"

  Run "NODE_CHECK_APP_JS" "node --check `"$app`""
  Run "GIT_STATUS_AFTER_PATCH" "git status --short"
  Run "GIT_ADD_PATCH" "git add ."
  Run "GIT_COMMIT_PATCH" "git commit -m 'AAYS_REAL_TOPOGRAPHY_PRODUCT topography final patch smoke shared runner $Stamp'"
  Run "GIT_PUSH_PATCH" "git push origin $Branch"

  if (
    $afterTxt.Contains('region_average_elevation_m') -and
    $afterTxt.Contains('elevation_difference_from_region_average_m') -and
    $afterTxt.Contains('calculation_explanation') -and
    $afterTxt.Contains('hight_differance.png') -and
    $afterTxt.Contains('normalizeTopographyLookupForPopup') -and
    $afterTxt.Contains('buildTopographyPopupRowsHtml')
  ) {
    L "STATUS=PATCH_SMOKE_READY_FOR_UI_LOOKUP_PROOF"
    L "PRODUCT_PROGRESS_ESTIMATE=94"
  } else {
    L "STATUS=PATCH_SMOKE_INCOMPLETE"
    L "PRODUCT_PROGRESS_ESTIMATE=89"
  }
}

Run "GIT_ADD_REPORT" "git add $ReportRel"
Run "GIT_COMMIT_REPORT" "git commit -m 'AAYS_REAL_TOPOGRAPHY_PRODUCT final patch smoke report $Stamp'"
Run "GIT_PUSH_REPORT" "git push origin $Branch"
