# CURRENT TASK — Topography / Elevation Difference panel patch

Branch: `feature/terrayield-aays-integration`
Repo root: `C:\Users\cagda\Documents\GitHub\AAYS`
Target file: `england_map_web/app.js`

## Safety rules

- Apply only a narrow frontend patch to `england_map_web/app.js`.
- Do not run DB write, migration, import, DDL, deploy, or fake/demo data generation.
- Preserve topography overlay lifecycle and parcel lookup lifecycle separation.
- Use exact-anchor replacement. If any anchor is missing, stop and write a diagnostic report instead of broad rewrite.
- After patch, run `node --check england_map_web\app.js`.
- Then run the read-only audit script if available:
  `powershell -ExecutionPolicy Bypass -File "terrayield_land_intelligence\docs\chatgpt_handoff\topography_elevation_panel_low_credit_20260612\07_LOCAL_READONLY_AUDIT.ps1"`

## Why this task exists

Current GitHub `england_map_web/app.js` was fetched by ChatGPT. Verified anchors:

- Topography menu item still uses `./assets/icons/worth-waves.svg`.
- `fetchParcelElevationForPopup(feature)` caches only numeric `center_elevation_m` in `parcelElevationCache`.
- `buildParcelPopupContent(feature, lngLat)` calculates elevation from a numeric feature/cache value only.
- Sales-only popup has a broken/out-of-scope reference:
  `parcelElevationCache?.get?.(parcelId) ?? properties?.topography_lookup ?? properties?.elevation_lookup ?? properties`
- Normal popup only shows `Denizden yukseklik` and not the required regional average/difference/source/confidence/matching/calculation fields.

## Required frontend behavior

When a user selects a parcel and opens the Topography/Elevation section in the existing parcel popup/panel, show, at minimum:

- `center_elevation_m` / sea-level elevation
- `region_average_elevation_m`
- `elevation_difference_from_region_average_m`
- `region_scope_type`, `region_scope_value`, `region_sample_count`
- `source_dataset` or `topography_source`
- `source_date` or `calculated_at`
- `datum`
- `confidence_level`, `confidence_reason`
- `matching_method`
- `calculation_explanation`

Use safe fallback text `Veri yok` for unavailable final fields and `Veri bekleniyor` while lookup is pending.

## Exact patch plan

### 1) Icon binding

Replace:

```js
{ id: "topography", label: "Yukselti", iconUrl: "./assets/icons/worth-waves.svg" },
```

with:

```js
{ id: "topography", label: "Yukselti", iconUrl: "./assets/icons/terrayield_icons/hight_differance.png" },
```

### 2) Add popup lookup helpers

Insert the following helper block immediately before `async function fetchParcelElevationForPopup(feature) {` unless already present:

```js
function normalizeTopographyLookupForPopup(value) {
  if (value == null) return null;
  const raw = value && value.data && typeof value.data === "object" ? value.data : value;
  if (typeof raw === "number") {
    return Number.isFinite(raw) ? {
      layer_name: "Topography",
      center_elevation_m: raw,
      elevation_above_sea_level_m: raw,
      region_average_elevation_m: null,
      elevation_difference_from_region_average_m: null,
    } : null;
  }
  if (!raw || typeof raw !== "object") return null;
  const n = (candidate) => {
    const numeric = Number(candidate);
    return Number.isFinite(numeric) ? numeric : null;
  };
  const centerElevation = n(raw.center_elevation_m ?? raw.elevation_above_sea_level_m ?? raw.elevation_m ?? raw.height_m ?? raw.altitude_m);
  const regionAverage = n(raw.region_average_elevation_m);
  let regionDifference = n(raw.elevation_difference_from_region_average_m);
  if (!Number.isFinite(regionDifference) && Number.isFinite(centerElevation) && Number.isFinite(regionAverage)) {
    regionDifference = centerElevation - regionAverage;
  }
  const hasAnyTopographyValue = [centerElevation, regionAverage, regionDifference].some((candidate) => Number.isFinite(candidate));
  if (!hasAnyTopographyValue) return null;
  return {
    ...raw,
    layer_name: raw.layer_name || "Topography",
    center_elevation_m: centerElevation,
    elevation_above_sea_level_m: n(raw.elevation_above_sea_level_m) ?? centerElevation,
    region_average_elevation_m: regionAverage,
    elevation_difference_from_region_average_m: regionDifference,
    region_scope_type: raw.region_scope_type ?? null,
    region_scope_value: raw.region_scope_value ?? null,
    region_sample_count: n(raw.region_sample_count),
    elevation_difference_class: raw.elevation_difference_class || raw.class_level || null,
    color_hex: raw.color_hex || raw.color_category || null,
    source_dataset: raw.source_dataset || null,
    topography_source: raw.topography_source || raw.source_dataset || null,
    source_date: raw.source_date || null,
    calculated_at: raw.calculated_at || null,
    confidence_level: raw.confidence_level || null,
    confidence_reason: raw.confidence_reason || null,
    matching_method: raw.matching_method || null,
    datum: raw.datum || null,
    source_resolution_m: n(raw.source_resolution_m),
    calculation_explanation: raw.calculation_explanation || null,
  };
}

function getTopographyLookupForPopup(feature) {
  const props = feature?.properties || {};
  const cacheKey = getParcelElevationCacheKey(feature);
  const cachedLookup = cacheKey ? normalizeTopographyLookupForPopup(parcelElevationCache.get(cacheKey)) : null;
  return cachedLookup
    || normalizeTopographyLookupForPopup(props.topography_lookup)
    || normalizeTopographyLookupForPopup(props.elevation_lookup)
    || normalizeTopographyLookupForPopup(props);
}

function formatTopographyMeterValue(value, fallbackText = "Veri yok", signed = false) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return fallbackText;
  const prefix = signed && numeric > 0 ? "+" : "";
  return `${prefix}${formatNumber(numeric, 2)} m`;
}

function formatTopographyScopeValue(lookup) {
  if (!lookup) return "Veri yok";
  const scopeType = lookup.region_scope_type || "scope_yok";
  const scopeValue = lookup.region_scope_value ?? "-";
  const sampleCount = Number.isFinite(Number(lookup.region_sample_count)) ? formatNumber(Number(lookup.region_sample_count), 0) : "-";
  return `${scopeType}=${scopeValue}, sample=${sampleCount}`;
}

function firstNonEmptyTopographyText(...values) {
  for (const value of values) {
    if (value !== null && value !== undefined && String(value).trim() !== "") {
      return String(value).trim();
    }
  }
  return "Veri yok";
}

function buildTopographyPopupRowsHtml(lookup, pendingText = "Veri bekleniyor", mode = "div") {
  const sourceText = firstNonEmptyTopographyText(lookup?.topography_source, lookup?.source_dataset);
  const sourceDateText = firstNonEmptyTopographyText(lookup?.source_date, lookup?.calculated_at);
  const confidenceText = lookup
    ? `${firstNonEmptyTopographyText(lookup.confidence_level)} - ${firstNonEmptyTopographyText(lookup.confidence_reason)}`
    : "Veri yok";
  const rows = [
    ["Deniz seviyesinden yukseklik", formatTopographyMeterValue(lookup?.center_elevation_m, pendingText)],
    ["Bolgesel ortalama yukseklik", formatTopographyMeterValue(lookup?.region_average_elevation_m)],
    ["Bolgesel ortalamadan fark", formatTopographyMeterValue(lookup?.elevation_difference_from_region_average_m, "Veri yok", true)],
    ["Bolge hesabi", formatTopographyScopeValue(lookup)],
    ["Kaynak", sourceText],
    ["Kaynak tarihi", sourceDateText],
    ["Datum", firstNonEmptyTopographyText(lookup?.datum)],
    ["Guven", confidenceText],
    ["Matching method", firstNonEmptyTopographyText(lookup?.matching_method)],
    ["Hesap", firstNonEmptyTopographyText(lookup?.calculation_explanation)],
  ];
  if (mode === "br") {
    return rows.map(([label, value]) => `${escapeHtml(label)}: ${escapeHtml(value)}`).join("<br />");
  }
  return rows.map(([label, value]) => `<div><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</div>`).join("");
}
```

### 3) Cache full lookup object

Inside `fetchParcelElevationForPopup(feature)`, replace the numeric-only block:

```js
const payload = await response.json();
const data = payload && payload.data && typeof payload.data === "object" ? payload.data : payload;
const elevation = Number(data?.center_elevation_m);
if (Number.isFinite(elevation)) {
  parcelElevationCache.set(cacheKey, elevation);
}
```

with:

```js
const payload = await response.json();
const data = payload && payload.data && typeof payload.data === "object" ? payload.data : payload;
const lookup = normalizeTopographyLookupForPopup(data);
if (lookup) {
  parcelElevationCache.set(cacheKey, lookup);
}
```

### 4) Popup variable binding

In `buildParcelPopupContent(feature, lngLat)`, replace numeric cache variable calculation with:

```js
const elevationFromFeature = getParcelElevationFromFeature(feature);
const topographyLookup = getTopographyLookupForPopup(feature);
const parcelElevationMeters = Number.isFinite(Number(topographyLookup?.center_elevation_m))
  ? Number(topographyLookup.center_elevation_m)
  : (Number.isFinite(Number(elevationFromFeature)) ? Number(elevationFromFeature) : null);
const parcelElevationText = Number.isFinite(parcelElevationMeters)
  ? `${formatNumber(parcelElevationMeters, 2)} m`
  : "Veri bekleniyor";
const topographyPopupRowsHtml = buildTopographyPopupRowsHtml(topographyLookup, parcelElevationText, "div");
const topographyPopupRowsBreakHtml = buildTopographyPopupRowsHtml(topographyLookup, parcelElevationText, "br");
```

### 5) Sales-only popup rows

Replace both the old `Denizden yukseklik` line and the broken `parcelId/properties` difference row with:

```js
${topographyPopupRowsHtml}
```

### 6) Normal popup rows

Replace:

```js
Denizden yukseklik: ${parcelElevationText}<br />
```

with:

```js
${topographyPopupRowsBreakHtml}<br />
```

## Required report

Write a report under:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/`

Report must include:

```text
status=PATCH_APPLIED or PATCH_BLOCKED
branch=feature/terrayield-aays-integration
file=england_map_web/app.js
node_check=PASS/FAIL
db_write=false
migration=false
production_deploy=false
fake_data=false
local_readonly_audit=PASS/FAIL/NOT_RUN
```

If blocked, include the missing anchor and leave `app.js` unchanged.
