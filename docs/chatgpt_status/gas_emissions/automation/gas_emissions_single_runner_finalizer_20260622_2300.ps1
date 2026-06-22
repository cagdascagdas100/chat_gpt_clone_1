$ErrorActionPreference = 'Continue'
$PageRoot = 'docs/chatgpt_status/gas_emissions'
$StatusPath = Join-Path $PageRoot 'status/gas_emissions_finalizer_status_20260622_2300.json'
$ReportPath = Join-Path $PageRoot 'reports/gas_emissions_finalizer_result_20260622_2300.md'
$HeartbeatPath = Join-Path $PageRoot 'heartbeat/gas_emissions_finalizer_heartbeat_20260622_2300.json'
$TaskId = 'gas-emissions-single-runner-finalizer-20260622_2300'
$Now = Get-Date -Format o
New-Item -ItemType Directory -Force (Split-Path $StatusPath) | Out-Null
New-Item -ItemType Directory -Force (Split-Path $ReportPath) | Out-Null
New-Item -ItemType Directory -Force (Split-Path $HeartbeatPath) | Out-Null
function Write-JsonFile($Path, $Object) { $Object | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $Path }
function Probe-Url($Name, $Url) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 8 -Uri $Url
    return @{ name=$Name; url=$Url; ok=($r.StatusCode -ge 200 -and $r.StatusCode -lt 300); status_code=[int]$r.StatusCode; error='' }
  } catch {
    return @{ name=$Name; url=$Url; ok=$false; status_code=0; error=$_.Exception.Message }
  }
}
Write-JsonFile $HeartbeatPath @{ schema_version='aays.heartbeat.v1'; page_key='gas_emissions'; task_id=$TaskId; state='runner_script_started'; updated_at=$Now }
$AppPath = 'england_map_web/app.js'
$DataPath = 'england_map_web/data/parcel_emissions_scores.geojson'
$IconPath = 'england_map_web/assets/icons/terrayield_icons/air.png'
$nodeCheck = $false; $nodeOutput = ''
try { $nodeOutput = (& node --check $AppPath 2>&1 | Out-String).Trim(); $nodeCheck = ($LASTEXITCODE -eq 0) } catch { $nodeOutput = $_.Exception.Message }
$appText = if (Test-Path $AppPath) { Get-Content -Raw -Encoding UTF8 $AppPath } else { '' }
$markers = @{
  has_gas_bridge = $appText.Contains('AAYS_GAS_EMISSIONS')
  has_gas_source = $appText.Contains('GAS_EMISSIONS_SOURCE_ID')
  has_data_url = $appText.Contains('GAS_EMISSIONS_DATA_URL')
  has_popup_builder = $appText.Contains('buildGasEmissionsPopupMetaHtml')
  has_polygon_builder = $appText.Contains('buildVisiblePolygonFeatures')
  has_direct_source_true = $appText.Contains('const directSourceMode = true')
  has_direct_source_false = $appText.Contains('const directSourceMode = false')
  has_geometry_polygon_join = $appText.Contains('polygon_join')
  has_air_icon = $appText.Contains('assets/icons/terrayield_icons/air.png')
}
$requiredFieldNames = @('emission_percent','emission_level','emission_color_hex','confidence','source_type','source_date','matching_method','calculation_explanation')
$requiredFieldHits = @{}
foreach ($f in $requiredFieldNames) { $requiredFieldHits[$f] = $appText.Contains($f) }
$dataExists = Test-Path $DataPath; $featureCount = 0; $sampleGasRecordHasFields = $false
if ($dataExists) {
  try {
    $json = Get-Content -Raw -Encoding UTF8 $DataPath | ConvertFrom-Json
    if ($json.features) {
      $features = @($json.features); $featureCount = $features.Count
      $firstProps = $features | ForEach-Object { $_.properties } | Where-Object { $_ } | Select-Object -First 1
      if ($firstProps) { $sampleGasRecordHasFields = [bool]($firstProps.emission_percent -or $firstProps.emission_level -or $firstProps.confidencePercent -or $firstProps.source_type) }
    }
  } catch { $featureCount = -1 }
}
$iconExists = Test-Path $IconPath
$httpProbes = @(
  (Probe-Url 'health' 'http://127.0.0.1:8010/health'),
  (Probe-Url 'app' 'http://127.0.0.1:8010/england_map_web/?r=gas-finalizer'),
  (Probe-Url 'geojson' 'http://127.0.0.1:8010/england_map_web/data/parcel_emissions_scores.geojson?v=20260622-gas-emissions-v2'),
  (Probe-Url 'air_icon' 'http://127.0.0.1:8010/england_map_web/assets/icons/terrayield_icons/air.png')
)
$httpReady = -not (@($httpProbes | Where-Object { -not $_.ok }).Count -gt 0)
$browser = @{ attempted=$false; playwright_available=$false; ok=$false; geometry_mode=''; gas_fields_visible=$false; error='' }
try {
  $smokeJs = @'
(async () => {
  const out = {attempted:true, playwright_available:false, ok:false, geometry_mode:'', gas_fields_visible:false, error:''};
  try { require.resolve('playwright'); out.playwright_available = true; } catch (e) { out.error = 'playwright_not_available'; console.log(JSON.stringify(out)); return; }
  const { chromium } = require('playwright');
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage();
    await page.goto('http://127.0.0.1:8010/england_map_web/?r=gas-finalizer', {waitUntil:'networkidle', timeout:20000});
    await page.waitForTimeout(3000);
    const r = await page.evaluate(async () => {
      const bridge = window.AAYS_GAS_EMISSIONS || null;
      if (bridge && typeof bridge.enable === 'function') { await bridge.enable(); }
      if (bridge && typeof bridge.toggle === 'function') { await bridge.toggle(true); }
      await new Promise((resolve) => setTimeout(resolve, 3000));
      const state = bridge && typeof bridge.getState === 'function' ? bridge.getState() : null;
      const text = document.body ? document.body.innerText : '';
      const labels = ['emission_percent','emission_level','emission_color_hex','confidence','source_type','source_date','matching_method','calculation_explanation'];
      return {hasBridge:!!bridge, state, geometryMode: state && state.geometryMode || '', gasFieldsVisible: labels.some((x) => text.includes(x))};
    });
    out.ok = !!r.hasBridge;
    out.geometry_mode = r.geometryMode || '';
    out.gas_fields_visible = !!r.gasFieldsVisible;
  } catch (e) { out.error = String(e && e.message || e); }
  await browser.close();
  console.log(JSON.stringify(out));
})();
'@
  $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('gas_finalizer_smoke_' + [guid]::NewGuid().ToString('N') + '.js')
  $smokeJs | Set-Content -Encoding UTF8 $tmp
  $browserRaw = (& node $tmp 2>&1 | Out-String).Trim()
  Remove-Item -Force $tmp -ErrorAction SilentlyContinue
  if ($browserRaw) { $browser = $browserRaw | ConvertFrom-Json }
} catch { $browser = @{ attempted=$true; playwright_available=$false; ok=$false; geometry_mode=''; gas_fields_visible=$false; error=$_.Exception.Message } }
$staticReady = $nodeCheck -and $dataExists -and ($featureCount -gt 0) -and $iconExists -and $markers.has_gas_bridge -and $markers.has_gas_source -and $markers.has_data_url -and $markers.has_popup_builder -and $markers.has_polygon_builder -and $markers.has_direct_source_false -and (-not $markers.has_direct_source_true)
$runtimeReady = $httpReady -and $browser.ok -and ($browser.geometry_mode -eq 'polygon_join') -and $browser.gas_fields_visible
$finalReady = $staticReady -and $runtimeReady
if ($finalReady) { $status='FINAL_READY'; $percent=100; $can100=$true }
elseif ($staticReady -and $httpReady) { $status='STATIC_AND_HTTP_READY_BROWSER_PROOF_REQUIRED'; $percent=92; $can100=$false }
elseif ($staticReady) { $status='STATIC_READY_RUNTIME_PROOF_REQUIRED'; $percent=90; $can100=$false }
else { $status='PARTIAL_STATIC_BLOCKERS_DETECTED'; $percent=86; $can100=$false }
$blockers = @()
if (-not $nodeCheck) { $blockers += 'node_check_failed' }
if (-not $dataExists) { $blockers += 'gas_geojson_missing' }
if ($featureCount -le 0) { $blockers += 'gas_geojson_feature_count_not_positive' }
if (-not $iconExists) { $blockers += 'air_icon_missing' }
if (-not $staticReady) { $blockers += 'static_gas_markers_incomplete' }
if (-not $httpReady) { $blockers += 'http_200_health_app_geojson_icon_not_proven' }
if (-not $browser.ok) { $blockers += 'browser_bridge_not_proven' }
if ($browser.geometry_mode -ne 'polygon_join') { $blockers += 'runtime_geometryMode_polygon_join_not_proven' }
if (-not $browser.gas_fields_visible) { $blockers += 'parcel_popup_or_side_panel_non_empty_gas_fields_not_proven' }
$statusObj = @{
  schema_version='aays.status.v2'; page_key='gas_emissions'; task_id=$TaskId; status=$status; completion_percent=$percent; can_mark_100_percent=$can100;
  node_check_pass=$nodeCheck; node_check_output=$nodeOutput; data_exists=$dataExists; data_feature_count=$featureCount; sample_gas_record_has_fields=$sampleGasRecordHasFields; icon_exists=$iconExists;
  static_ready=$staticReady; http_ready=$httpReady; runtime_ready=$runtimeReady; final_ready=$finalReady; markers=$markers; required_field_hits=$requiredFieldHits; http_probes=$httpProbes; browser_probe=$browser; blockers=$blockers; updated_at=(Get-Date -Format o)
}
Write-JsonFile $StatusPath $statusObj
$report = @()
$report += '# Gas Emissions Finalizer Result - Enhanced Runner Probe'
$report += ''
$report += "STATUS=$status"
$report += "COMPLETION_PERCENT=$percent"
$report += "CAN_MARK_100_PERCENT=$can100"
$report += "NODE_CHECK_PASS=$nodeCheck"
$report += "DATA_EXISTS=$dataExists"
$report += "DATA_FEATURE_COUNT=$featureCount"
$report += "ICON_EXISTS=$iconExists"
$report += "STATIC_READY=$staticReady"
$report += "HTTP_READY=$httpReady"
$report += "RUNTIME_READY=$runtimeReady"
$report += "BROWSER_GEOMETRY_MODE=$($browser.geometry_mode)"
$report += "BROWSER_GAS_FIELDS_VISIBLE=$($browser.gas_fields_visible)"
$report += ''
$report += '## HTTP probes'
foreach ($p in $httpProbes) { $report += "- $($p.name): ok=$($p.ok) status=$($p.status_code) url=$($p.url) error=$($p.error)" }
$report += ''
$report += '## Blockers'
foreach ($b in $blockers) { $report += "- $b" }
$report += ''
$report += '## Stop rule'
$report += 'FINAL_READY requires static_ready=true, http_ready=true, runtime_ready=true, geometryMode=polygon_join, and visible non-empty gas popup/side-panel proof.'
$report | Set-Content -Encoding UTF8 $ReportPath
Write-JsonFile $HeartbeatPath @{ schema_version='aays.heartbeat.v1'; page_key='gas_emissions'; task_id=$TaskId; state='runner_script_finished'; status=$status; completion_percent=$percent; can_mark_100_percent=$can100; updated_at=(Get-Date -Format o) }
if ($finalReady) { exit 0 } else { exit 2 }
