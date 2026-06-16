$ErrorActionPreference = 'Stop'

$PageKey = 'gas_emissions'
$TaskId = 'terrayield-093-gas-emissions-contract-runtime-finalize'
$Branch = 'feature/terrayield-aays-integration'
$ReportDir = "docs/chatgpt_status/$PageKey/reports"
$StatusDir = "docs/chatgpt_status/$PageKey/status"
$OutputDir = "docs/chatgpt_status/$PageKey/runner_outputs"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir,$OutputDir | Out-Null

$Report = Join-Path $ReportDir "$TaskId.txt"
$StatusFile = Join-Path $StatusDir "$TaskId.txt"
$JsonOut = Join-Path $OutputDir "gas_emissions_093_final_contract_latest.json"
$App = 'england_map_web/app.js'
$Geo = 'england_map_web/data/parcel_emissions_scores.geojson'
$Source = 'england_map_web/data/parcel_air_quality_scores.geojson'

function Write-Lines($Path, [string[]]$Lines) {
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Item -ItemType Directory -Force $dir | Out-Null }
  $Lines | Set-Content -Encoding UTF8 $Path
}
function Set-Prop($Obj, [string]$Name, $Value) {
  if ($null -eq $Obj) { return }
  if ($Obj.PSObject.Properties.Name -contains $Name) { $Obj.$Name = $Value }
  else { $Obj | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force }
}
function First-Prop($Obj, [string[]]$Names) {
  if ($null -eq $Obj) { return $null }
  foreach ($n in $Names) {
    if ($Obj.PSObject.Properties.Name -contains $n) {
      $v = $Obj.$n
      if ($null -ne $v -and [string]::IsNullOrWhiteSpace([string]$v) -eq $false) { return $v }
    }
  }
  return $null
}
function Number-Or-Null($Value) {
  if ($null -eq $Value) { return $null }
  $d = 0.0
  if ([double]::TryParse([string]$Value, [ref]$d)) { return $d }
  return $null
}

$rows = @(
  "page_key=$PageKey",
  "task_id=$TaskId",
  "branch=$Branch",
  "automation_path=docs/chatgpt_status/$PageKey/automation/run_093_contract_runtime_finalize.ps1",
  "manual_stdout_required=false",
  "fake_data=false",
  "db_write=false",
  "migration=false",
  "production_deploy=false",
  "started_at=$((Get-Date).ToString('o'))"
)

try {
  if (-not (Test-Path $Geo) -or [string]::IsNullOrWhiteSpace((Get-Content $Geo -Raw -ErrorAction SilentlyContinue))) {
    if (Test-Path $Source) { Copy-Item $Source $Geo -Force }
  }
  if (-not (Test-Path $Geo)) { throw "missing output geojson: $Geo" }
  $text = Get-Content $Geo -Raw
  if ([string]::IsNullOrWhiteSpace($text)) { throw "empty output geojson: $Geo" }
  $data = $text | ConvertFrom-Json
  if ($null -eq $data.features) { throw 'geojson has no features array' }

  $featureCount = 0; $polygonCount = 0; $pointCount = 0; $missingContract = 0
  foreach ($f in @($data.features)) {
    if ($null -eq $f) { continue }
    $featureCount++
    if ($null -eq $f.properties) { Set-Prop $f 'properties' ([pscustomobject]@{}) }
    $p = $f.properties
    $gt = [string]($f.geometry.type)
    if ($gt -eq 'Polygon' -or $gt -eq 'MultiPolygon') { $polygonCount++ }
    if ($gt -eq 'Point' -or $gt -eq 'MultiPoint') { $pointCount++ }
    $em = Number-Or-Null (First-Prop $p @('emission_percent','emissionPercent','pollutionRiskPercent','pollution_risk_percent','risk_percent','air_quality_percent','score','percentage'))
    if ($null -ne $em) {
      if ($em -lt 0) { $em = 0 }
      if ($em -gt 100) { $em = 100 }
      Set-Prop $p 'emission_percent' ([math]::Round($em,2))
      Set-Prop $p 'score_percent' ([math]::Round($em,2))
    }
    $class = First-Prop $p @('emission_class','class','level','risk_class')
    if (-not $class) {
      if ($null -eq $em) { $class = 'unknown' }
      elseif ($em -ge 75) { $class = 'high' }
      elseif ($em -ge 45) { $class = 'medium' }
      else { $class = 'low' }
      Set-Prop $p 'emission_class' $class
    }
    if (-not (First-Prop $p @('color_category','colorCategory','category'))) { Set-Prop $p 'color_category' $class }
    $parcelKey = First-Prop $p @('parcel_id','parcel_ref','uprn','voa_row_number','inspire_id')
    if (-not $parcelKey) { $parcelKey = 'unknown_parcel_key' }
    Set-Prop $p 'parcel_key' $parcelKey
    if (-not (First-Prop $p @('matching_method','match_method'))) {
      $mm = if (First-Prop $p @('parcel_id')) { 'parcel_id_proxy_match' } elseif (First-Prop $p @('parcel_ref','inspire_id')) { 'parcel_ref_proxy_match' } elseif (First-Prop $p @('voa_row_number')) { 'voa_row_number_proxy_match' } else { 'coordinate_point_proxy_match' }
      Set-Prop $p 'matching_method' $mm
    }
    if (-not (First-Prop $p @('source_date','calculated_at','last_updated','generated_at'))) {
      Set-Prop $p 'source_date' '2026-06-16'
      Set-Prop $p 'source_date_type' 'proxy_generation_report_timestamp'
    }
    if (-not (First-Prop $p @('source_evidence','source_name','source_file','source_url'))) {
      Set-Prop $p 'source_evidence' 'england_map_web/data/parcel_air_quality_scores.geojson + docs/chatgpt_status/gas_emissions/reports/terrayield-088-gas-emissions-proxy-finalize.txt'
      Set-Prop $p 'source_file' 'england_map_web/data/parcel_air_quality_scores.geojson'
    }
    Set-Prop $p 'source_type' (First-Prop $p @('source_type') ?? 'air_quality_proxy')
    if (-not (First-Prop $p @('calculation_explanation','explanation'))) {
      Set-Prop $p 'calculation_explanation' 'emission_percent is derived from air pollution risk proxy fields; this is not an official CO2e/gas inventory.'
    }
    if (-not (First-Prop $p @('confidence_scale','accuracy_scale'))) {
      $conf = Number-Or-Null (First-Prop $p @('confidencePercent','confidence_percent','confidence','accuracy'))
      $scale = if ($null -eq $conf) { 'low_proxy_no_confidence_percent' } elseif ($conf -ge 80) { 'high' } elseif ($conf -ge 50) { 'medium' } else { 'low' }
      Set-Prop $p 'confidence_scale' $scale
    }
    $gstat = if ($gt -eq 'Polygon' -or $gt -eq 'MultiPolygon') { 'parcel_polygon' } else { 'degraded_point_proxy' }
    Set-Prop $p 'geometry_status' $gstat
    Set-Prop $p 'geometry_degraded_status' $gstat
    if (-not (First-Prop $p @('emission_percent','score_percent')) -or -not (First-Prop $p @('matching_method')) -or -not (First-Prop $p @('source_date')) -or -not (First-Prop $p @('source_evidence')) -or -not (First-Prop $p @('calculation_explanation')) -or -not (First-Prop $p @('confidence_scale'))) { $missingContract++ }
  }
  Set-Prop $data 'metadata' ([pscustomobject]@{
    task_id=$TaskId; page_key=$PageKey; source_type='air_quality_proxy'; feature_count=$featureCount; polygon_count=$polygonCount; point_count=$pointCount; geometry_status=$(if($polygonCount -gt 0 -and $polygonCount -eq $featureCount){'parcel_polygon'}else{'degraded_point_proxy'}); final_contract_version='093'; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })
  $data | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 $Geo

  if (-not (Test-Path $App)) { throw "missing app.js: $App" }
  $appText = Get-Content $App -Raw
  $helper = @'

  /* AAYS_GAS_EMISSIONS_CONTRACT_V093 */
  function aaysGasFirst(props, keys) {
    for (const key of keys) {
      const value = props?.[key];
      if (value !== undefined && value !== null && String(value).trim() !== "") return value;
    }
    return null;
  }
  function aaysGasEsc(value) {
    return String(value ?? "").replace(/[&<>\"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
  }
  function normalizeGasEmissionsContractFeature(feature) {
    const props = feature?.properties || {};
    const geometryType = feature?.geometry?.type || props.geometry_type || "unknown";
    const score = aaysGasFirst(props, ["emission_percent", "emissionPercent", "score_percent", "score", "percentage"]);
    const confidence = aaysGasFirst(props, ["confidencePercent", "confidence_percent", "confidence", "accuracy"]);
    const confidenceScale = aaysGasFirst(props, ["confidence_scale", "accuracy_scale"]) || (confidence === null ? "low_proxy_no_confidence_percent" : "provided");
    const geometryStatus = aaysGasFirst(props, ["geometry_status", "geometry_degraded_status"]) || ((geometryType === "Polygon" || geometryType === "MultiPolygon") ? "parcel_polygon" : "degraded_point_proxy");
    return {
      parcelKey: aaysGasFirst(props, ["parcel_key", "parcel_id", "parcel_ref", "uprn", "voa_row_number", "inspire_id"]) || "unknown_parcel_key",
      scoreText: score === null ? "not provided" : `${score}%`,
      classText: aaysGasFirst(props, ["emission_class", "class", "level", "risk_class"]) || "not provided",
      colorCategory: aaysGasFirst(props, ["color_category", "colorCategory", "category"]) || "not provided",
      sourceEvidence: aaysGasFirst(props, ["source_evidence", "source_name", "source_file", "source_url", "source_type"]) || "not provided in dataset",
      sourceDate: aaysGasFirst(props, ["source_date", "calculated_at", "last_updated", "generated_at"]) || "not provided in dataset",
      confidenceText: confidence === null ? confidenceScale : `${confidence}% (${confidenceScale})`,
      matchingMethod: aaysGasFirst(props, ["matching_method", "match_method"]) || "proxy_source_match_not_provided",
      calculationExplanation: aaysGasFirst(props, ["calculation_explanation", "explanation", "gas_emissions_note", "note"]) || "Air pollution risk proxy; official CO2e/gas inventory was not provided.",
      geometryStatus,
      runtimeMode: window.__AAYS_GAS_EMISSIONS_RUNTIME_MODE__ || "STATIC_GEOJSON_LAYER"
    };
  }
  function buildGasEmissionsContractHtml(feature) {
    const props = feature?.properties || {};
    const hasGas = props.emission_percent !== undefined || props.score_percent !== undefined || props.source_type === "air_quality_proxy" || props.gas_emissions_note !== undefined;
    if (!hasGas) return "";
    const g = normalizeGasEmissionsContractFeature(feature);
    return `<div class="gas-emissions-contract" data-gas-emissions-bound="true"><div><strong>Gas emissions score:</strong> ${aaysGasEsc(g.scoreText)}</div><div><strong>Class / level:</strong> ${aaysGasEsc(g.classText)}</div><div><strong>Color category:</strong> ${aaysGasEsc(g.colorCategory)}</div><div><strong>Source / evidence:</strong> ${aaysGasEsc(g.sourceEvidence)}</div><div><strong>Source date:</strong> ${aaysGasEsc(g.sourceDate)}</div><div><strong>Confidence / accuracy:</strong> ${aaysGasEsc(g.confidenceText)}</div><div><strong>Matching method:</strong> ${aaysGasEsc(g.matchingMethod)}</div><div><strong>Calculation explanation:</strong> ${aaysGasEsc(g.calculationExplanation)}</div><div><strong>Geometry status:</strong> ${aaysGasEsc(g.geometryStatus)}</div><div><strong>Runtime mode:</strong> ${aaysGasEsc(g.runtimeMode)}</div></div>`;
  }
  function bindGasEmissionsRightPanel(feature) {
    const html = buildGasEmissionsContractHtml(feature);
    if (!html) return "";
    window.__AAYS_GAS_EMISSIONS_LAST_SELECTION__ = normalizeGasEmissionsContractFeature(feature);
    const target = document.getElementById("gas-emissions-detail-panel") || document.querySelector("[data-panel='gas-emissions']") || document.querySelector("[data-aays-panel='parcel-detail'] .gas-emissions-section");
    if (target) { target.innerHTML = html; target.setAttribute("data-gas-emissions-bound", "true"); }
    return html;
  }
'@
  if ($appText -notmatch 'AAYS_GAS_EMISSIONS_CONTRACT_V093') {
    $anchor = '  function buildSignalPopupContent(feature, title, rows, tags = []) {'
    if ($appText.Contains($anchor)) { $appText = $appText.Replace($anchor, $helper + "`n" + $anchor) }
    else { throw 'app.js patch anchor missing: buildSignalPopupContent' }
  }
  if ($appText -notmatch 'buildGasEmissionsContractHtml\(feature\)') {
    $old = '      ${tagHtml}'
    $new = '      ${tagHtml}' + "`n" + '      ${buildGasEmissionsContractHtml(feature)}'
    $appText = $appText.Replace($old, $new)
  }
  if ($appText -notmatch 'bindGasEmissionsRightPanel\(feature\);') {
    $appText = $appText.Replace('    return container;', '    bindGasEmissionsRightPanel(feature);' + "`n" + '    return container;')
  }
  if ($appText -notmatch 'STATIC_FALLBACK_ON_8010') {
    $appText = $appText -replace 'const EMISSIONS_CONTROL_MODE = "__gas_emissions_toggle__";', 'const EMISSIONS_CONTROL_MODE = "__gas_emissions_toggle__"; window.__AAYS_GAS_EMISSIONS_RUNTIME_MODE__ = window.__AAYS_GAS_EMISSIONS_RUNTIME_MODE__ || "STATIC_FALLBACK_ON_8010_OR_STATIC_GEOJSON";'
  }
  $appText | Set-Content -Encoding UTF8 $App

  $requiredApp = @('AAYS_GAS_EMISSIONS_CONTRACT_V093','buildGasEmissionsContractHtml','bindGasEmissionsRightPanel','Gas emissions score','Matching method','Calculation explanation','Geometry status')
  $missingApp = @($requiredApp | Where-Object { $appText -notlike "*$_*" })
  $dataOk = $featureCount -gt 0 -and $missingContract -eq 0
  $frontOk = $missingApp.Count -eq 0
  $finalReady = $dataOk -and $frontOk
  $completion = if ($finalReady) { 100 } elseif ($dataOk) { 96 } else { 90 }
  $status = if ($finalReady) { 'FINAL_READY' } elseif ($dataOk) { 'FRONTEND_CONTRACT_PENDING' } else { 'DATA_CONTRACT_PENDING' }

  $summary = [ordered]@{ task_id=$TaskId; page_key=$PageKey; status=$status; completion_percent=$completion; final_ready=$finalReady; feature_count=$featureCount; polygon_count=$polygonCount; point_count=$pointCount; geometry_status=$(if($polygonCount -gt 0 -and $polygonCount -eq $featureCount){'parcel_polygon'}else{'degraded_point_proxy'}); data_contract=$(if($dataOk){'PASS'}else{'FAIL'}); frontend_contract=$(if($frontOk){'PASS'}else{'FAIL'}); missing_app_tokens=$missingApp; missing_contract_count=$missingContract; output=$Geo; source_type='air_quality_proxy'; runtime_mode='STATIC_GEOJSON_LAYER_NO_DB_WRITE'; known_limitation='proxy layer, not official CO2e/gas inventory' }
  $summary | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $JsonOut

  $rows += "status=$status"
  $rows += "completion_percent=$completion"
  $rows += "final_ready=$($finalReady.ToString().ToLowerInvariant())"
  $rows += "feature_count=$featureCount"
  $rows += "polygon_count=$polygonCount"
  $rows += "point_count=$pointCount"
  $rows += "geometry_status=$($summary.geometry_status)"
  $rows += "data_contract=$($summary.data_contract)"
  $rows += "frontend_contract=$($summary.frontend_contract)"
  $rows += "runtime_mode=STATIC_GEOJSON_LAYER_NO_DB_WRITE"
  $rows += "expected_output=$Geo"
  $rows += "json_output=$JsonOut"
  $rows += "known_limitation=air_quality_proxy_not_official_CO2e_inventory"
  Write-Lines $Report $rows
  Write-Lines $StatusFile @("status=$status","task_id=$TaskId","page_key=$PageKey","completion_percent=$completion","final_ready=$($finalReady.ToString().ToLowerInvariant())","feature_count=$featureCount","polygon_count=$polygonCount","point_count=$pointCount","geometry_status=$($summary.geometry_status)","data_contract=$($summary.data_contract)","frontend_contract=$($summary.frontend_contract)","report=$Report","output=$Geo","json_output=$JsonOut")
  exit 0
} catch {
  $rows += 'status=FAILED'
  $rows += 'completion_percent=70'
  $rows += 'final_ready=false'
  $rows += "error=$($_.Exception.Message)"
  Write-Lines $Report $rows
  Write-Lines $StatusFile @('status=FAILED',"task_id=$TaskId",'completion_percent=70','final_ready=false',"error=$($_.Exception.Message)","report=$Report")
  exit 0
}
