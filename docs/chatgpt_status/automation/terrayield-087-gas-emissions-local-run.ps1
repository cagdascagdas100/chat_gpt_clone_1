$ErrorActionPreference = "Continue"

$repo = "C:\Users\cagda\Documents\GitHub\AAYS"
$branch = "feature/terrayield-aays-integration"
$taskId = "terrayield-087-gas-emissions-air-icon-integration"
$frontend = Join-Path $repo "england_map_web"
$appJs = Join-Path $frontend "app.js"
$inputGeojson = Join-Path $frontend "data\parcel_air_quality_scores.geojson"
$outRoot = "E:\AAYS_DATA\emissions_air_quality"
$outDir = Join-Path $outRoot "outputs"
$manifestDir = Join-Path $outRoot "manifests"
$reportDir = Join-Path $repo "docs\chatgpt_status\reports"
$runnerOutDir = Join-Path $repo "docs\chatgpt_status\runner_outputs"
$heartbeatDir = Join-Path $repo "docs\chatgpt_status\heartbeat"
$statusDir = Join-Path $repo "docs\chatgpt_status\status"

New-Item -ItemType Directory -Force -Path $outDir,$manifestDir,$reportDir,$runnerOutDir,$heartbeatDir,$statusDir,(Join-Path $frontend "data") | Out-Null

$reportTxt = Join-Path $reportDir "$taskId.txt"
$reportJson = Join-Path $reportDir "$taskId.json"
$runnerJson = Join-Path $runnerOutDir "$taskId.json"
$latestJson = Join-Path $runnerOutDir "latest_output.json"
$heartbeat = Join-Path $heartbeatDir "$taskId.txt"
$statusTxt = Join-Path $statusDir "$taskId.txt"

$generatedAt = (Get-Date).ToUniversalTime().ToString("o")
$progress = 40
$status = "RUNNING"
$errors = @()
$featureCount = 0
$dataGenerated = $false
$appPatched = $false
$nodeCheckPass = $false
$staticSmokePass = $false
$openUrl = $null
$serverPid = $null

function LevelForRisk([object]$v) {
  if ($null -eq $v -or $v -eq "") { return @("VERI_YOK", "Veri Yok", "#9e9e9e") }
  $n = [double]$v
  if ($n -le 20) { return @("COK_DUSUK", "Cok Dusuk", "#2e7d32") }
  if ($n -le 40) { return @("DUSUK", "Dusuk", "#8bc34a") }
  if ($n -le 60) { return @("ORTA", "Orta", "#fdd835") }
  if ($n -le 80) { return @("YUKSEK", "Yuksek", "#fb8c00") }
  return @("COK_YUKSEK", "Cok Yuksek", "#c62828")
}
function CsvEsc([object]$v) {
  if ($null -eq $v) { return "" }
  $s = [string]$v
  $s = $s.Replace('"','""')
  if ($s.Contains(',') -or $s.Contains('"') -or $s.Contains("`n") -or $s.Contains("`r")) { return '"' + $s + '"' }
  return $s
}

try {
  Set-Location $repo
  git checkout $branch | Out-Null 2>&1
  git pull origin $branch | Out-Null 2>&1
} catch { $errors += "git_sync_failed: $($_.Exception.Message)" }

if (-not (Test-Path $inputGeojson)) {
  $status = "BLOCKED_MISSING_LOCAL_INPUT"
  $errors += "Missing input_proxy_geojson=$inputGeojson"
} else {
  try {
    $geo = Get-Content $inputGeojson -Raw | ConvertFrom-Json
    $featureCount = @($geo.features).Count
    $csv = New-Object System.Collections.Generic.List[string]
    $csv.Add("parcel_id,lon,lat,emission_percent,emission_level,emission_level_label_tr,emission_color_hex,confidence_percent,source_type,method_id,calculated_at,airQualityPercent_raw,pollutionRiskPercent_raw") | Out-Null
    foreach ($f in $geo.features) {
      $p = $f.properties
      $risk = $p.pollutionRiskPercent
      if ($null -eq $risk -and $null -ne $p.airQualityPercent) { $risk = [math]::Round(100 - [double]$p.airQualityPercent, 2) }
      $lvl = LevelForRisk $risk
      $p | Add-Member -Force -NotePropertyName emission_percent -NotePropertyValue $risk
      $p | Add-Member -Force -NotePropertyName emission_level -NotePropertyValue $lvl[0]
      $p | Add-Member -Force -NotePropertyName emission_level_label_tr -NotePropertyValue $lvl[1]
      $p | Add-Member -Force -NotePropertyName emission_color_hex -NotePropertyValue $lvl[2]
      $p | Add-Member -Force -NotePropertyName confidence_percent -NotePropertyValue $p.confidencePercent
      $p | Add-Member -Force -NotePropertyName source_type -NotePropertyValue "air_quality_proxy"
      $p | Add-Member -Force -NotePropertyName method_id -NotePropertyValue "aq_proxy_pollution_risk_v1"
      $p | Add-Member -Force -NotePropertyName calculated_at -NotePropertyValue $generatedAt
      $p | Add-Member -Force -NotePropertyName source_name -NotePropertyValue "Local proxy air-quality score"
      $p | Add-Member -Force -NotePropertyName method_summary_tr -NotePropertyValue "Hava kalitesi/kirlilik riski proxy verisinden turetilmistir; resmi CO2e/sera gazi envanteri degildir."
      $parcelId = $p.parcel_id; if ($null -eq $parcelId) { $parcelId = $p.id }; if ($null -eq $parcelId) { $parcelId = $p.parcelId }
      $coords = $f.geometry.coordinates
      $csv.Add((@($parcelId,$coords[0],$coords[1],$risk,$lvl[0],$lvl[1],$lvl[2],$p.confidencePercent,"air_quality_proxy","aq_proxy_pollution_risk_v1",$generatedAt,$p.airQualityPercent,$p.pollutionRiskPercent) | ForEach-Object { CsvEsc $_ }) -join ",") | Out-Null
    }
    $geoJsonOutLocal = Join-Path $outDir "parcel_emissions_scores.geojson"
    $csvOutLocal = Join-Path $outDir "parcel_emissions_scores.csv"
    $manifestLocal = Join-Path $outDir "parcel_emissions_score_manifest.json"
    $geo | ConvertTo-Json -Depth 100 | Set-Content -Encoding utf8 $geoJsonOutLocal
    ($csv -join "`n") | Set-Content -Encoding utf8 $csvOutLocal
    @{schema_name="aays_parcel_emissions_score_v1";status="DATA_READY";source_type="air_quality_proxy";method_id="aq_proxy_pollution_risk_v1";feature_count=$featureCount;calculated_at=$generatedAt;db_write=$false;migration=$false;production_deploy=$false;fake_data=$false;warning="Proxy only; not official CO2e/GHG"} | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 $manifestLocal
    Copy-Item $geoJsonOutLocal (Join-Path $frontend "data\parcel_emissions_scores.geojson") -Force
    Copy-Item $csvOutLocal (Join-Path $frontend "data\parcel_emissions_scores.csv") -Force
    Copy-Item $manifestLocal (Join-Path $frontend "data\parcel_emissions_score_manifest.json") -Force
    "source_id,source_type,notes`nsrc_existing_parcel_air_quality_scores,air_quality_proxy,Local proxy input; not official CO2e/GHG" | Set-Content -Encoding utf8 (Join-Path $manifestDir "source_registry.csv")
    @{evidence_id="ev_existing_air_quality_proxy_001";source_id="src_existing_parcel_air_quality_scores";collected_at=$generatedAt;verdict="usable_as_proxy"} | ConvertTo-Json -Compress | Set-Content -Encoding utf8 (Join-Path $manifestDir "evidence_manifest.jsonl")
    $dataGenerated = $true; $progress = 60
  } catch { $status = "DATA_GENERATION_FAILED"; $errors += $_.Exception.Message }
}

if ($dataGenerated -and (Test-Path $appJs)) {
  try {
    $app = Get-Content $appJs -Raw
    $marker = "AAYS_GAS_EMISSIONS_PROXY_INTEGRATION_V2"
    if ($app -notmatch [regex]::Escape($marker)) {
      $integrationBlock = @'

  // AAYS_GAS_EMISSIONS_PROXY_INTEGRATION_V2
  const GAS_EMISSIONS_SOURCE_ID = "gas-emissions-air-quality-proxy-source";
  const GAS_EMISSIONS_LAYER_ID = "gas-emissions-air-quality-proxy-layer";
  const GAS_EMISSIONS_DATA_URL = "./data/parcel_emissions_scores.geojson";
  const GAS_EMISSIONS_LEGEND_ID = "gas-emissions-air-quality-proxy-legend";
  let gasEmissionsVisible = false;
  let gasEmissionsLoadPromise = null;

  function gasEmissionsColorExpression() {
    return [
      "case",
      ["!", ["has", "emission_percent"]], "#9e9e9e",
      ["<=", ["to-number", ["get", "emission_percent"]], 20], "#2e7d32",
      ["<=", ["to-number", ["get", "emission_percent"]], 40], "#8bc34a",
      ["<=", ["to-number", ["get", "emission_percent"]], 60], "#fdd835",
      ["<=", ["to-number", ["get", "emission_percent"]], 80], "#fb8c00",
      "#c62828",
    ];
  }

  function ensureGasEmissionsLegend() {
    let el = document.getElementById(GAS_EMISSIONS_LEGEND_ID);
    if (!el) {
      el = document.createElement("div");
      el.id = GAS_EMISSIONS_LEGEND_ID;
      el.className = "map-overlay-legend gas-emissions-legend";
      el.innerHTML = [
        "<strong>Gaz Emisyonu (proxy)</strong>",
        "<div><span style='background:#2e7d32'></span>0-20 Cok Dusuk</div>",
        "<div><span style='background:#8bc34a'></span>21-40 Dusuk</div>",
        "<div><span style='background:#fdd835'></span>41-60 Orta</div>",
        "<div><span style='background:#fb8c00'></span>61-80 Yuksek</div>",
        "<div><span style='background:#c62828'></span>81-100 Cok Yuksek</div>",
        "<div><span style='background:#9e9e9e'></span>Veri Yok</div>",
        "<small>Kaynak: air_quality_proxy; resmi CO2e/GHG degildir.</small>",
      ].join("");
      document.body.appendChild(el);
    }
    el.style.display = gasEmissionsVisible ? "block" : "none";
  }

  async function ensureGasEmissionsLayer() {
    if (gasEmissionsLoadPromise) return gasEmissionsLoadPromise;
    gasEmissionsLoadPromise = (async () => {
      const response = await fetch(GAS_EMISSIONS_DATA_URL, { cache: "no-store" });
      if (!response.ok) throw new Error(`Gaz emisyonu dosyasi yuklenemedi: HTTP ${response.status}`);
      const data = await response.json();
      if (!map.getSource(GAS_EMISSIONS_SOURCE_ID)) {
        map.addSource(GAS_EMISSIONS_SOURCE_ID, { type: "geojson", data });
      } else {
        map.getSource(GAS_EMISSIONS_SOURCE_ID).setData(data);
      }
      if (!map.getLayer(GAS_EMISSIONS_LAYER_ID)) {
        map.addLayer({
          id: GAS_EMISSIONS_LAYER_ID,
          type: "circle",
          source: GAS_EMISSIONS_SOURCE_ID,
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 3, 14, 8],
            "circle-color": gasEmissionsColorExpression(),
            "circle-opacity": 0.78,
            "circle-stroke-color": "#263238",
            "circle-stroke-width": 0.7,
          },
          layout: { visibility: gasEmissionsVisible ? "visible" : "none" },
        });
        map.on("click", GAS_EMISSIONS_LAYER_ID, (event) => {
          const feature = event.features && event.features[0];
          if (!feature) return;
          const p = feature.properties || {};
          const html = [
            `<strong>Gaz Emisyonu</strong>`,
            `<div>Skor: <b>${p.emission_percent ?? "Veri Yok"}</b></div>`,
            `<div>Seviye: <b>${p.emission_level_label_tr || p.emission_level || "Veri Yok"}</b></div>`,
            `<div>Guven: <b>${p.confidence_percent ?? "-"}</b></div>`,
            `<div>Kaynak: <b>${p.source_type || "air_quality_proxy"}</b></div>`,
            `<div>Guncelleme: <b>${p.calculated_at || "-"}</b></div>`,
            `<small>Proxy veridir; resmi CO2e/GHG envanteri degildir.</small>`,
          ].join("");
          new maplibregl.Popup({ closeButton: true, closeOnClick: true })
            .setLngLat(event.lngLat)
            .setHTML(html)
            .addTo(map);
        });
        map.on("mouseenter", GAS_EMISSIONS_LAYER_ID, () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", GAS_EMISSIONS_LAYER_ID, () => { map.getCanvas().style.cursor = ""; });
      }
      return data;
    })();
    return gasEmissionsLoadPromise;
  }

  async function setGasEmissionsVisible(visible) {
    gasEmissionsVisible = Boolean(visible);
    try {
      await ensureGasEmissionsLayer();
      if (map.getLayer(GAS_EMISSIONS_LAYER_ID)) {
        map.setLayoutProperty(GAS_EMISSIONS_LAYER_ID, "visibility", gasEmissionsVisible ? "visible" : "none");
      }
      ensureGasEmissionsLegend();
      emitLayerRuntimeEvent("gas_emissions", gasEmissionsVisible ? "visible" : "hidden", GAS_EMISSIONS_DATA_URL);
      if (typeof showStatus === "function") showStatus(gasEmissionsVisible ? "Gaz emisyonu proxy katmani acildi." : "Gaz emisyonu proxy katmani kapatildi.", false);
    } catch (error) {
      emitLayerRuntimeEvent("gas_emissions", "error", error?.message || String(error));
      if (typeof showThrottledStatus === "function") showThrottledStatus("gas-emissions", `Gaz emisyonu katmani acilamadi: ${error?.message || error}`, true, 3000);
    }
  }

  window.AAYS_GAS_EMISSIONS_LAYER = { setVisible: setGasEmissionsVisible, ensure: ensureGasEmissionsLayer };
  window.addEventListener("aays:toggle-gas-emissions", () => setGasEmissionsVisible(!gasEmissionsVisible));
  document.querySelectorAll(`[data-map-mode="${EMISSIONS_CONTROL_MODE}"], [data-layer-mode="${EMISSIONS_CONTROL_MODE}"], [value="${EMISSIONS_CONTROL_MODE}"]`).forEach((el) => {
    el.addEventListener("click", () => setGasEmissionsVisible(!gasEmissionsVisible));
    el.addEventListener("change", () => setGasEmissionsVisible(Boolean(el.checked)));
  });

'@
      $closurePattern = "(?s)\r?\n\}\)\(\);\s*$"
      if ([regex]::IsMatch($app, $closurePattern)) {
        $app = [regex]::Replace($app, $closurePattern, "`n$integrationBlock`n})();`n")
      } else {
        $app += "`n$integrationBlock`n"
      }
      Set-Content -Encoding utf8 -Path $appJs -Value $app
    }
    $verifiedApp = Get-Content $appJs -Raw
    if ($verifiedApp -match [regex]::Escape($marker) -and $verifiedApp -match "parcel_emissions_scores.geojson" -and $verifiedApp -match "AAYS_GAS_EMISSIONS_LAYER") {
      $appPatched = $true; $progress = 75
    } else {
      $status = "APP_PATCH_VERIFICATION_FAILED"; $errors += "Gas emissions UI marker/layer not found after patch"
    }
  } catch { $status = "APP_PATCH_FAILED"; $errors += $_.Exception.Message }
}

if ($appPatched) {
  try {
    node --check "england_map_web\app.js" *> (Join-Path $reportDir "terrayield-087-node-check.txt")
    if ($LASTEXITCODE -eq 0) { $nodeCheckPass = $true; $progress = 85 } else { $errors += "node_check_failed" }
  } catch { $errors += "node_check_exception: $($_.Exception.Message)" }
}

if ($nodeCheckPass) {
  try {
    $port = 8787
    Push-Location $frontend
    $server = Start-Process -FilePath "python" -ArgumentList "-m http.server $port --bind 127.0.0.1" -RedirectStandardOutput (Join-Path $reportDir "terrayield-087-http-server-out.txt") -RedirectStandardError (Join-Path $reportDir "terrayield-087-http-server-err.txt") -PassThru -NoNewWindow
    Start-Sleep -Seconds 3
    $page = Invoke-WebRequest -UseBasicParsing -TimeoutSec 20 -Uri "http://127.0.0.1:$port/"
    $data = Invoke-WebRequest -UseBasicParsing -TimeoutSec 20 -Uri "http://127.0.0.1:$port/data/parcel_emissions_scores.geojson"
    if ($page.StatusCode -eq 200 -and $data.Content -match "emission_percent") {
      $staticSmokePass = $true; $progress = 100; $status = "FINAL_READY"; $openUrl = "http://127.0.0.1:$port/"; $serverPid = $server.Id; Start-Process $openUrl
    } else {
      $status = "STATIC_SMOKE_FAILED"; Stop-Process -Id $server.Id -Force
    }
    Pop-Location
  } catch { $status = "STATIC_SMOKE_EXCEPTION"; $errors += $_.Exception.Message; try { Pop-Location } catch {} }
}
if ($status -eq "RUNNING") { $status = if ($progress -eq 100) { "FINAL_READY" } else { "PARTIAL_OR_BLOCKED" } }

$text = @"
task_id=$taskId
status=$status
overall_progress_percent=$progress
feature_count=$featureCount
data_generated=$dataGenerated
app_patched=$appPatched
node_check_pass=$nodeCheckPass
static_smoke_pass=$staticSmokePass
local_app_url=$openUrl
local_server_pid=$serverPid
db_write=false
migration=false
production_deploy=false
fake_data=false
input_geojson=$inputGeojson
runtime_geojson=england_map_web/data/parcel_emissions_scores.geojson
runtime_csv=england_map_web/data/parcel_emissions_scores.csv
errors=$($errors -join " | ")
manual_stdout_required=false
next_action=$(if ($progress -eq 100) { "none" } else { "fix_local_input_or_patch_failure" })
"@
$text | Set-Content -Encoding utf8 $reportTxt
$nextActionValue = if ($progress -eq 100) { "none" } else { "fix_local_input_or_patch_failure" }
$obj = @{task_id=$taskId;status=$status;overall_progress_percent=$progress;feature_count=$featureCount;data_generated=$dataGenerated;app_patched=$appPatched;node_check_pass=$nodeCheckPass;static_smoke_pass=$staticSmokePass;local_app_url=$openUrl;local_server_pid=$serverPid;db_write=$false;migration=$false;production_deploy=$false;fake_data=$false;input_geojson=$inputGeojson;runtime_geojson="england_map_web/data/parcel_emissions_scores.geojson";runtime_csv="england_map_web/data/parcel_emissions_scores.csv";errors=$errors;manual_stdout_required=$false;next_action=$nextActionValue}
$obj | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 $reportJson
Copy-Item $reportJson $runnerJson -Force
Copy-Item $reportJson $latestJson -Force
"$(Get-Date -Format o) task_id=$taskId status=$status progress=$progress" | Set-Content -Encoding utf8 $heartbeat
$text | Set-Content -Encoding utf8 $statusTxt

git add england_map_web/app.js england_map_web/data/parcel_emissions_scores.geojson england_map_web/data/parcel_emissions_scores.csv england_map_web/data/parcel_emissions_score_manifest.json docs/chatgpt_status/reports docs/chatgpt_status/runner_outputs docs/chatgpt_status/heartbeat docs/chatgpt_status/status 2>$null
git commit -m "feat: run gas emissions air icon integration" | Out-Null 2>&1
git push origin $branch | Out-Null 2>&1
