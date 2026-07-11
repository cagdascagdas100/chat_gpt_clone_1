[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Write-Json([string]$Path, [object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText(
    $Path,
    (($Value | ConvertTo-Json -Depth 80) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
}

function Copy-Atomic([string]$Source, [string]$Target) {
  Ensure-Dir (Split-Path -Parent $Target)
  $tmp = $Target + '.aays_tmp_' + [Guid]::NewGuid().ToString('N')
  Copy-Item -LiteralPath $Source -Destination $tmp -Force
  Move-Item -LiteralPath $tmp -Destination $Target -Force
}

function Get-JsonRowCount([string]$Path) {
  $obj = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
  return @($obj.rows).Count
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$taskId = [string]$env:AAYS_TASK_ID
$pageKey = [string]$env:AAYS_PAGE_KEY
$branch = [string]$env:AAYS_TARGET_BRANCH

if (-not $repoRoot -or -not $taskId -or $pageKey -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_100_MUST_RUN_INSIDE_CANONICAL_SHARED_RUNNER'
}
if ($branch -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_100_WRONG_BRANCH'
}

$portableRoot = 'F:\TerraYield_AAYS_Portable'
$servedRepoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$rowsRel = 'england_map_web\data\program_layer_matrix\gas_emissions_visible_rows_latest.json'
$statusRel = 'england_map_web\data\program_layer_matrix\gas_emissions_status_latest.json'
$matrixRel = 'england_map_web\TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$rowsPath = Join-Path $repoRoot $rowsRel
$statusPath = Join-Path $repoRoot $statusRel
$matrixPath = Join-Path $repoRoot $matrixRel

foreach ($required in @($rowsPath,$statusPath,$matrixPath)) {
  if (-not (Test-Path -LiteralPath $required)) { throw "MISSING_REQUIRED_FILE: $required" }
}

$initialCount = Get-JsonRowCount $rowsPath
if ($initialCount -ne 66 -and $initialCount -ne 100) {
  throw "WAITING_FOR_66_ROW_PREREQUISITE: current=$initialCount"
}

$sourceDir = Join-Path $portableRoot 'sources\gas_emissions'
Ensure-Dir $sourceDir
$sourceLocalPath = Join-Path $sourceDir '2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv'
$sourceUrl = 'https://assets.publishing.service.gov.uk/media/68653c7ee6c3cc924228943f/2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv'
if (-not (Test-Path -LiteralPath $sourceLocalPath) -or (Get-Item -LiteralPath $sourceLocalPath).Length -lt 50000000) {
  $downloadTmp = $sourceLocalPath + '.download_' + [Guid]::NewGuid().ToString('N')
  Invoke-WebRequest -Uri $sourceUrl -OutFile $downloadTmp -UseBasicParsing -TimeoutSec 600
  if ((Get-Item -LiteralPath $downloadTmp).Length -lt 50000000) {
    Remove-Item -LiteralPath $downloadTmp -Force -ErrorAction SilentlyContinue
    throw 'OFFICIAL_CSV_DOWNLOAD_TOO_SMALL'
  }
  Move-Item -LiteralPath $downloadTmp -Destination $sourceLocalPath -Force
}
$sourceSize = (Get-Item -LiteralPath $sourceLocalPath).Length
$sourceSha256 = (Get-FileHash -LiteralPath $sourceLocalPath -Algorithm SHA256).Hash.ToLowerInvariant()

# The first Hartlepool block is sufficient for the 2005 batches; avoid loading all 79 MB into memory.
$headLines = @([System.IO.File]::ReadLines($sourceLocalPath) | Select-Object -First 260)
$csvRows = @($headLines | ConvertFrom-Csv)

$manifestRels = @(
  'docs\chatgpt_status\gas_emissions\candidates\156_gas_emissions_official_agriculture_2005_candidates_20260711.json',
  'docs\chatgpt_status\gas_emissions\candidates\157_gas_emissions_official_lulucf_2005_candidates_20260711.json',
  'docs\chatgpt_status\gas_emissions\candidates\158_gas_emissions_official_transport_remaining_2005_candidates_20260711.json'
)

$verified = New-Object System.Collections.Generic.List[object]
foreach ($manifestRel in $manifestRels) {
  $manifestPath = Join-Path $repoRoot $manifestRel
  if (-not (Test-Path -LiteralPath $manifestPath)) { throw "MISSING_CANDIDATE_MANIFEST: $manifestRel" }
  $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
  foreach ($candidate in @($manifest.candidates)) {
    $match = @($csvRows | Where-Object {
      [string]$_.'Local Authority Code' -eq 'E06000001' -and
      [int]$_.'Calendar Year' -eq 2005 -and
      [string]$_.'LA GHG Sector' -eq [string]$candidate.sector -and
      [string]$_.'LA GHG Sub-sector' -eq [string]$candidate.sub_sector -and
      [string]$_.'Greenhouse gas' -eq [string]$candidate.greenhouse_gas
    })
    if ($match.Count -ne 1) {
      throw "OFFICIAL_CSV_MATCH_COUNT_NOT_ONE: $($candidate.row_id) count=$($match.Count)"
    }
    $m = $match[0]
    $actualTerritorial = [double]$m.'Territorial emissions (kt CO2e)'
    $actualScope = [double]$m.'Emissions within the scope of influence of LAs (kt CO2)'
    if ([Math]::Abs($actualTerritorial - [double]$candidate.territorial_emissions_kt_co2e) -gt 0.000000001) {
      throw "TERRITORIAL_VALUE_MISMATCH: $($candidate.row_id)"
    }
    if ([Math]::Abs($actualScope - [double]$candidate.scope_of_influence_kt_co2) -gt 0.000000001) {
      throw "SCOPE_VALUE_MISMATCH: $($candidate.row_id)"
    }
    $verified.Add([ordered]@{
      row_id = [string]$candidate.row_id
      calendar_year = 2005
      sector = [string]$candidate.sector
      sub_sector = [string]$candidate.sub_sector
      greenhouse_gas = [string]$candidate.greenhouse_gas
      territorial_emissions_kt_co2e = $actualTerritorial
      scope_of_influence_kt_co2 = $actualScope
      source_lines = [string]$candidate.source_preview_line
      matching_method = 'official_govuk_preview_plus_downloaded_csv_exact_fields'
      calculation_explanation = "Official GOV.UK preview $($candidate.source_preview_line) and downloaded CSV exact-key/value match; no parcel allocation or derived calculation applied."
      confidence_percent = 94
      accuracy_score_4 = '3.4/4'
      needs_manual_review = $true
      parcel_binding_status = 'PENDING'
      source_url = [string]$manifest.source_page_url
      source_download_url = $sourceUrl
      source_local_raw_path = $sourceLocalPath
      source_local_sha256 = $sourceSha256
      source_manifest_path = ($manifestRel -replace '\\','/')
      source_path = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
      visible_rows_artifact_path = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
      status_path = 'england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
      report_path = 'docs/chatgpt_status/gas_emissions/reports/159_gas_emissions_100_multi_batch_pipeline_20260711.json'
      changed_in_latest_run = $true
      is_new_in_latest_batch = $true
      display_badge = 'KAYNAKLI_YENI'
      served_commit_sha = 'PENDING_RUNNER_COMMIT'
      artifact_sha = 'SEE_STATUS_ARTIFACT_SHA256'
    })
  }
}
if ($verified.Count -ne 34) { throw "VERIFIED_CANDIDATE_COUNT_NOT_34: $($verified.Count)" }

$visible = Get-Content -LiteralPath $rowsPath -Raw -Encoding UTF8 | ConvertFrom-Json
$existing = @($visible.rows)
$targetIds = @($verified | ForEach-Object { [string]$_.row_id })
$oldRows = @($existing | Where-Object { $targetIds -notcontains [string]$_.row_id })
foreach ($row in $oldRows) {
  $row.changed_in_latest_run = $false
  $row.is_new_in_latest_batch = $false
  $row.display_badge = 'KAYNAKLI_MEVCUT'
}
$visible.rows = @($oldRows) + @($verified)
if (@($visible.rows).Count -ne 100) { throw "TARGET_VISIBLE_ROW_COUNT_NOT_100: $(@($visible.rows).Count)" }
$visible.status = 'OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_100'
$visible.previous_visible_row_count = 66
$visible.previous_visible_rows_count = 66
$visible.new_rows_added_this_run = 34
$visible.new_rows_in_latest_batch = 34
$visible.visible_row_count = 100
$visible.visible_rows_count = 100
$visible.latest_batch_id = 'gas_emissions_official_agriculture_lulucf_transport_2005_20260711_01'
$visible.source_row_accuracy_score_4 = '3.4/4'
$visible.accuracy_note = '100 official GOV.UK local-authority rows; the latest 34 passed preview-line plus downloaded-CSV exact-key/value checks. Parcel binding remains pending.'
$visible.source_local_raw_path = $sourceLocalPath
$visible | Add-Member -NotePropertyName source_local_sha256 -NotePropertyValue $sourceSha256 -Force
$visible | Add-Member -NotePropertyName source_local_size_bytes -NotePropertyValue $sourceSize -Force
$visible | Add-Member -NotePropertyName browser_smoke_passed_for_100_rows -NotePropertyValue $false -Force
$visible.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$visible.final_ready = $false
$visible.product_final_ready = $false
$visible.fake_data = $false
Write-Json $rowsPath $visible

$artifactSha256 = (Get-FileHash -LiteralPath $rowsPath -Algorithm SHA256).Hash.ToLowerInvariant()
$canonical = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
$canonical.status = 'OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_100_PENDING_BROWSER_SMOKE'
$canonical.visible_rows_count = 100
$canonical.previous_visible_row_count = 66
$canonical.new_rows_added_this_run = 34
$canonical.current_visible_change_rows = 34
$canonical.verification_score_after = '3.4/4'
$canonical.source_local_raw_path = $sourceLocalPath
$canonical | Add-Member -NotePropertyName source_local_sha256 -NotePropertyValue $sourceSha256 -Force
$canonical | Add-Member -NotePropertyName source_local_size_bytes -NotePropertyValue $sourceSize -Force
$canonical | Add-Member -NotePropertyName artifact_sha256 -NotePropertyValue $artifactSha256 -Force
$canonical.browser_smoke_passed = $false
$canonical.parcel_binding_gate_passed = $false
$canonical.final_ready = $false
$canonical.product_final_ready = $false
$canonical.fake_data = $false
$canonical.db_write = $false
$canonical.migration = $false
$canonical.production_deploy = $false
$canonical.updated_at = (Get-Date).ToUniversalTime().ToString('o')
Write-Json $statusPath $canonical

foreach ($item in @(
  @{ Source=$rowsPath; Target=(Join-Path $servedRepoRoot $rowsRel) },
  @{ Source=$statusPath; Target=(Join-Path $servedRepoRoot $statusRel) },
  @{ Source=$matrixPath; Target=(Join-Path $servedRepoRoot $matrixRel) }
)) {
  Copy-Atomic $item.Source $item.Target
}

$httpRowsUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json?gas100=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$httpCount = -1
$httpError = $null
for ($i=0; $i -lt 15; $i++) {
  try {
    $resp = Invoke-RestMethod -Uri $httpRowsUrl -Method Get -TimeoutSec 20 -Headers @{ 'Cache-Control'='no-cache' }
    $httpCount = @($resp.rows).Count
    if ($httpCount -eq 100) { break }
  } catch { $httpError = $_.Exception.Message }
  Start-Sleep -Seconds 2
}
if ($httpCount -ne 100) { throw "HTTP_8012_ROW_COUNT_NOT_100: $httpCount $httpError" }

# Non-destructive parcel GeoJSON field audit. This does not invent parcel allocations.
$geoCandidates = @(
  (Join-Path $repoRoot 'england_map_web\data\parcel_emissions_scores.geojson'),
  (Join-Path $repoRoot 'england_map_web\data\parcel_air_quality_scores.geojson')
)
$geoPath = $geoCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$geoAudit = [ordered]@{ path='NOT_FOUND'; feature_count=0; complete_feature_count=0; required_fields=@('emission_percent','level','risk_color','confidence','source','source_date','matching_method','calculation_explanation') }
if ($geoPath) {
  $geo = Get-Content -LiteralPath $geoPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $features = @($geo.features)
  $requiredFields = @($geoAudit.required_fields)
  $complete = 0
  foreach ($feature in $features) {
    $props = $feature.properties
    $ok = $true
    foreach ($field in $requiredFields) {
      if ($null -eq $props.$field -or [string]::IsNullOrWhiteSpace([string]$props.$field)) { $ok = $false; break }
    }
    if ($ok) { $complete++ }
  }
  $geoAudit.path = $geoPath
  $geoAudit.feature_count = $features.Count
  $geoAudit.complete_feature_count = $complete
}

$appPath = Join-Path $repoRoot 'england_map_web\app.js'
$appText = if (Test-Path -LiteralPath $appPath) { Get-Content -LiteralPath $appPath -Raw -Encoding UTF8 } else { '' }
$uiAudit = [ordered]@{
  app_js_path = if ($appText) { $appPath } else { 'NOT_FOUND' }
  air_icon_reference = ($appText -match 'air\.png')
  emission_percent_reference = ($appText -match 'emission_percent')
  legend_reference = ($appText -match 'legend')
  level_reference = ($appText -match '\blevel\b')
  risk_color_reference = ($appText -match 'risk_color')
  confidence_reference = ($appText -match 'confidence')
  source_date_reference = ($appText -match 'source_date')
  matching_method_reference = ($appText -match 'matching_method')
  calculation_explanation_reference = ($appText -match 'calculation_explanation')
}

$expectedIdsPath = Join-Path ([System.IO.Path]::GetTempPath()) ($taskId + '_expected_ids.json')
Write-Json $expectedIdsPath @($targetIds)
$tmpPy = Join-Path ([System.IO.Path]::GetTempPath()) ($taskId + '_browser.py')
$tmpOut = Join-Path ([System.IO.Path]::GetTempPath()) ($taskId + '_browser.json')
$pythonSource = @'
import json
import sys
import time
from pathlib import Path

out_path = Path(sys.argv[1])
expected_ids = set(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8-sig")))
url = "http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=gas100&ts=" + str(int(time.time()))
result = {"status":"FAIL","url":url,"expected_row_count":100,"unique_row_count":0,"new_marker_count":0,"manual_marker_on_new_count":0,"page_infos":[],"console_errors":[],"error":None}
driver = None
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1400")
    options.set_capability("goog:loggingPrefs", {"browser":"ALL"})
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    wait = WebDriverWait(driver, 60)
    wait.until(lambda d: d.find_element(By.ID, "layerSelect"))
    Select(driver.find_element(By.ID, "layerSelect")).select_by_value("gas")
    wait.until(lambda d: "100 satır" in d.find_element(By.ID, "pageInfo").text)
    row_map = {}
    for page_no in range(1, 5):
        wait.until(lambda d, p=page_no: f"Sayfa {p} / 4" in d.find_element(By.ID, "pageInfo").text)
        result["page_infos"].append(driver.find_element(By.ID, "pageInfo").text.strip())
        for row in driver.find_elements(By.CSS_SELECTOR, "#table tbody tr"):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                rid = cells[1].text.strip()
                if rid:
                    row_map[rid] = cells[0].text.strip()
        if page_no < 4:
            driver.find_element(By.ID, "next").click()
    severe = []
    try:
        severe = [e for e in driver.get_log("browser") if str(e.get("level", "")).upper() == "SEVERE"]
    except Exception:
        severe = []
    new_count = sum(1 for rid in expected_ids if "YENİ / LATEST" in row_map.get(rid, ""))
    manual_count = sum(1 for rid in expected_ids if "MANUEL İNCELEME" in row_map.get(rid, ""))
    passed = len(row_map) == 100 and expected_ids.issubset(row_map) and new_count == 34 and manual_count == 34 and not severe
    result.update({"status":"PASS" if passed else "FAIL","unique_row_count":len(row_map),"rendered_row_ids":sorted(row_map),"new_marker_count":new_count,"manual_marker_on_new_count":manual_count,"console_errors":severe,"title":driver.title})
    if not passed:
        result["error"] = "row_count_expected_ids_markers_or_console_check_failed"
except Exception as exc:
    result["error"] = f"{type(exc).__name__}: {exc}"
finally:
    if driver is not None:
        try: driver.quit()
        except Exception: pass
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
sys.exit(0 if result["status"] == "PASS" else 1)
'@
[System.IO.File]::WriteAllText($tmpPy, $pythonSource, [System.Text.UTF8Encoding]::new($false))
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
  & $python.Source $tmpPy $tmpOut $expectedIdsPath
} else {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if (-not $py) { throw 'PYTHON_NOT_FOUND_FOR_100_ROW_SELENIUM' }
  & $py.Source -3 $tmpPy $tmpOut $expectedIdsPath
}
$browserExit = $LASTEXITCODE
if (-not (Test-Path -LiteralPath $tmpOut)) { throw 'SELENIUM_100_RESULT_NOT_WRITTEN' }
$browser = Get-Content -LiteralPath $tmpOut -Raw -Encoding UTF8 | ConvertFrom-Json
$browserPassed = ($browserExit -eq 0 -and [string]$browser.status -eq 'PASS' -and [int]$browser.unique_row_count -eq 100 -and [int]$browser.new_marker_count -eq 34)

$reportRel = 'docs/chatgpt_status/gas_emissions/reports/159_gas_emissions_100_multi_batch_pipeline_20260711.json'
$resultStatusRel = 'docs/chatgpt_status/gas_emissions/status/159_gas_emissions_100_multi_batch_pipeline_latest.json'
$reportPath = Join-Path $repoRoot ($reportRel -replace '/', '\')
$resultStatusPath = Join-Path $repoRoot ($resultStatusRel -replace '/', '\')
$payload = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  status = if ($browserPassed) { 'PASS_100_VISIBLE_ROWS' } else { 'FAIL_100_BROWSER_GATE' }
  generated_by_runner = $true
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  target_branch = $branch
  initial_visible_rows = $initialCount
  verified_new_rows = 34
  visible_rows_after = 100
  source_url = $sourceUrl
  source_local_raw_path = $sourceLocalPath
  source_local_size_bytes = $sourceSize
  source_local_sha256 = $sourceSha256
  artifact_sha256 = $artifactSha256
  official_dual_match_passed = $true
  browser = $browser
  parcel_geojson_audit = $geoAudit
  ui_reference_audit = $uiAudit
  parcel_binding_gate_passed = $false
  single_runner_only = $true
  new_runner = $false
  parallel_runner = $false
  git_push_status = 'pending_runner_wrapper'
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json $reportPath $payload
Write-Json $resultStatusPath $payload

if ($browserPassed) {
  $canonical = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $canonical.status = 'OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_100_BROWSER_PASS'
  $canonical.browser_smoke_passed = $true
  $canonical | Add-Member -NotePropertyName browser_smoke_row_count -NotePropertyValue 100 -Force
  $canonical | Add-Member -NotePropertyName browser_smoke_new_marker_count -NotePropertyValue 34 -Force
  $canonical | Add-Member -NotePropertyName browser_smoke_report_path -NotePropertyValue $reportRel -Force
  $canonical | Add-Member -NotePropertyName browser_smoke_passed_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
  $canonical.next_required_runner_action = 'Begin evidence-based parcel matching only where a defensible spatial allocation method exists; do not infer local-authority totals onto parcels.'
  $canonical.final_ready = $false
  $canonical.product_final_ready = $false
  $canonical.fake_data = $false
  Write-Json $statusPath $canonical
  Copy-Atomic $statusPath (Join-Path $servedRepoRoot $statusRel)
}

Remove-Item -LiteralPath $tmpPy,$tmpOut,$expectedIdsPath -Force -ErrorAction SilentlyContinue
if (-not $browserPassed) { throw 'GAS_EMISSIONS_100_BROWSER_SMOKE_FAILED' }
Write-Output ($payload | ConvertTo-Json -Depth 80)
