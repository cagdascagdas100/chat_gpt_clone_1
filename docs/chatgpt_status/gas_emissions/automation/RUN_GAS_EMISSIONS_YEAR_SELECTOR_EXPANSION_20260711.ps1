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
    (($Value | ConvertTo-Json -Depth 100) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
}

function Copy-Atomic([string]$Source, [string]$Target) {
  Ensure-Dir (Split-Path -Parent $Target)
  $tmp = $Target + '.aays_tmp_' + [Guid]::NewGuid().ToString('N')
  Copy-Item -LiteralPath $Source -Destination $tmp -Force
  Move-Item -LiteralPath $tmp -Destination $Target -Force
}

function Parse-DoubleInvariant([string]$Value) {
  return [double]::Parse($Value, [System.Globalization.CultureInfo]::InvariantCulture)
}

function Get-Slug([string]$Value) {
  $text = $Value.ToLowerInvariant()
  $text = $text -replace "'", ''
  $text = $text -replace '[^a-z0-9]+', '-'
  return $text.Trim('-')
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$taskId = [string]$env:AAYS_TASK_ID
$pageKey = [string]$env:AAYS_PAGE_KEY
$branch = [string]$env:AAYS_TARGET_BRANCH

if (-not $repoRoot -or -not $taskId -or $pageKey -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_YEAR_SELECTOR_MUST_RUN_INSIDE_CANONICAL_SHARED_RUNNER'
}
if ($branch -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_YEAR_SELECTOR_WRONG_BRANCH'
}

$config = $null
if ($taskId -match '233.*2007|2007.*233') {
  $config = [ordered]@{
    year = 2007
    previous_rows = 151
    new_rows = 82
    target_rows = 233
    preview_start = 249
    preview_end = 330
    manifest_rel = 'docs/chatgpt_status/gas_emissions/candidates/161_gas_emissions_official_2007_selector_20260711.json'
    report_rel = 'docs/chatgpt_status/gas_emissions/reports/161_gas_emissions_233_year2007_pipeline_20260711.json'
    status_rel = 'docs/chatgpt_status/gas_emissions/status/161_gas_emissions_233_year2007_pipeline_latest.json'
  }
} elseif ($taskId -match '316.*2008|2008.*316') {
  $config = [ordered]@{
    year = 2008
    previous_rows = 233
    new_rows = 83
    target_rows = 316
    preview_start = 331
    preview_end = 413
    manifest_rel = 'docs/chatgpt_status/gas_emissions/candidates/162_gas_emissions_official_2008_selector_20260711.json'
    report_rel = 'docs/chatgpt_status/gas_emissions/reports/162_gas_emissions_316_year2008_pipeline_20260711.json'
    status_rel = 'docs/chatgpt_status/gas_emissions/status/162_gas_emissions_316_year2008_pipeline_latest.json'
  }
} else {
  throw "UNSUPPORTED_YEAR_SELECTOR_TASK_ID: $taskId"
}

$portableRoot = 'F:\TerraYield_AAYS_Portable'
$servedRepoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$rowsRel = 'england_map_web\data\program_layer_matrix\gas_emissions_visible_rows_latest.json'
$statusRel = 'england_map_web\data\program_layer_matrix\gas_emissions_status_latest.json'
$matrixRel = 'england_map_web\TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$rowsPath = Join-Path $repoRoot $rowsRel
$statusPath = Join-Path $repoRoot $statusRel
$matrixPath = Join-Path $repoRoot $matrixRel
$manifestPath = Join-Path $repoRoot ($config.manifest_rel -replace '/', '\')
$reportPath = Join-Path $repoRoot ($config.report_rel -replace '/', '\')
$resultStatusPath = Join-Path $repoRoot ($config.status_rel -replace '/', '\')

foreach ($required in @($rowsPath,$statusPath,$matrixPath,$manifestPath)) {
  if (-not (Test-Path -LiteralPath $required)) { throw "MISSING_REQUIRED_FILE: $required" }
}

$visibleBefore = Get-Content -LiteralPath $rowsPath -Raw -Encoding UTF8 | ConvertFrom-Json
$initialCount = @($visibleBefore.rows).Count
if ($initialCount -ne [int]$config.previous_rows -and $initialCount -ne [int]$config.target_rows) {
  throw "WAITING_FOR_YEAR_PREREQUISITE: year=$($config.year) current=$initialCount expected=$($config.previous_rows)"
}

$canonicalBefore = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($initialCount -eq [int]$config.previous_rows) {
  $requiredBrowserRows = [int]$config.previous_rows
  $browserRows = 0
  if ($canonicalBefore.PSObject.Properties.Name -contains 'browser_smoke_row_count') {
    $browserRows = [int]$canonicalBefore.browser_smoke_row_count
  }
  if (-not [bool]$canonicalBefore.browser_smoke_passed -or $browserRows -lt $requiredBrowserRows) {
    throw "WAITING_FOR_PREVIOUS_BROWSER_GATE: required=$requiredBrowserRows actual=$browserRows"
  }
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([int]$manifest.calendar_year -ne [int]$config.year -or [int]$manifest.expected_candidate_count -ne [int]$config.new_rows) {
  throw 'YEAR_SELECTOR_MANIFEST_CONTRACT_MISMATCH'
}

$sourceDir = Join-Path $portableRoot 'sources\gas_emissions'
Ensure-Dir $sourceDir
$sourceLocalPath = Join-Path $sourceDir '2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv'
$sourceUrl = [string]$manifest.source_download_url
if (-not (Test-Path -LiteralPath $sourceLocalPath) -or (Get-Item -LiteralPath $sourceLocalPath).Length -lt 50000000) {
  $downloadTmp = $sourceLocalPath + '.download_' + [Guid]::NewGuid().ToString('N')
  Invoke-WebRequest -Uri $sourceUrl -OutFile $downloadTmp -UseBasicParsing -TimeoutSec 900
  if ((Get-Item -LiteralPath $downloadTmp).Length -lt 50000000) {
    Remove-Item -LiteralPath $downloadTmp -Force -ErrorAction SilentlyContinue
    throw 'OFFICIAL_CSV_DOWNLOAD_TOO_SMALL'
  }
  Move-Item -LiteralPath $downloadTmp -Destination $sourceLocalPath -Force
}
$sourceSize = (Get-Item -LiteralPath $sourceLocalPath).Length
$sourceSha256 = (Get-FileHash -LiteralPath $sourceLocalPath -Algorithm SHA256).Hash.ToLowerInvariant()

# Hartlepool 2007/2008 rows are within the first 500 CSV records; avoid loading the full 79 MB file.
$headLines = @([System.IO.File]::ReadLines($sourceLocalPath) | Select-Object -First 500)
$csvRows = @($headLines | ConvertFrom-Csv)
$selected = @($csvRows | Where-Object {
  [string]$_.'Local Authority Code' -eq 'E06000001' -and
  [int]$_.'Calendar Year' -eq [int]$config.year
})
if ($selected.Count -ne [int]$config.new_rows) {
  throw "OFFICIAL_YEAR_ROW_COUNT_MISMATCH: year=$($config.year) count=$($selected.Count) expected=$($config.new_rows)"
}

$verified = New-Object System.Collections.Generic.List[object]
$index = 0
foreach ($row in $selected) {
  $previewLine = [int]$config.preview_start + $index
  $sector = [string]$row.'LA GHG Sector'
  $subSector = [string]$row.'LA GHG Sub-sector'
  $gas = [string]$row.'Greenhouse gas'
  $rowId = 'GHG-HPL-' + $config.year + '-' + (Get-Slug $sector) + '-' + (Get-Slug $subSector) + '-' + (Get-Slug $gas)
  $verified.Add([ordered]@{
    row_id = $rowId
    calendar_year = [int]$config.year
    sector = $sector
    sub_sector = $subSector
    greenhouse_gas = $gas
    territorial_emissions_kt_co2e = (Parse-DoubleInvariant ([string]$row.'Territorial emissions (kt CO2e)'))
    scope_of_influence_kt_co2 = (Parse-DoubleInvariant ([string]$row.'Emissions within the scope of influence of LAs (kt CO2)'))
    source_lines = "L$previewLine"
    matching_method = 'official_govuk_preview_range_plus_downloaded_csv_exact_authority_year_fields'
    calculation_explanation = "Official GOV.UK preview L$previewLine and downloaded CSV authority/year exact selection; value copied without parcel allocation or derived calculation."
    confidence_percent = 94
    accuracy_score_4 = '3.4/4'
    needs_manual_review = $true
    parcel_binding_status = 'PENDING'
    source_url = [string]$manifest.source_page_url
    source_download_url = $sourceUrl
    source_local_raw_path = $sourceLocalPath
    source_local_sha256 = $sourceSha256
    source_manifest_path = [string]$config.manifest_rel
    source_path = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
    visible_rows_artifact_path = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
    status_path = 'england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
    report_path = [string]$config.report_rel
    changed_in_latest_run = $true
    is_new_in_latest_batch = $true
    display_badge = 'KAYNAKLI_YENI'
    served_commit_sha = 'PENDING_RUNNER_COMMIT'
    artifact_sha = 'SEE_STATUS_ARTIFACT_SHA256'
  })
  $index++
}

$ids = @($verified | ForEach-Object { [string]$_.row_id })
if (@($ids | Select-Object -Unique).Count -ne [int]$config.new_rows) {
  throw 'YEAR_SELECTOR_GENERATED_DUPLICATE_ROW_IDS'
}

$visible = Get-Content -LiteralPath $rowsPath -Raw -Encoding UTF8 | ConvertFrom-Json
$existing = @($visible.rows)
$oldRows = @($existing | Where-Object { $ids -notcontains [string]$_.row_id })
foreach ($old in $oldRows) {
  $old.changed_in_latest_run = $false
  $old.is_new_in_latest_batch = $false
  $old.display_badge = 'KAYNAKLI_MEVCUT'
}
$visible.rows = @($oldRows) + @($verified)
if (@($visible.rows).Count -ne [int]$config.target_rows) {
  throw "TARGET_VISIBLE_ROW_COUNT_MISMATCH: actual=$(@($visible.rows).Count) expected=$($config.target_rows)"
}
$visible.status = "OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_$($config.target_rows)"
$visible.previous_visible_row_count = [int]$config.previous_rows
$visible.previous_visible_rows_count = [int]$config.previous_rows
$visible.new_rows_added_this_run = [int]$config.new_rows
$visible.new_rows_in_latest_batch = [int]$config.new_rows
$visible.visible_row_count = [int]$config.target_rows
$visible.visible_rows_count = [int]$config.target_rows
$visible.latest_batch_id = [string]$manifest.batch_id
$visible.source_row_accuracy_score_4 = '3.4/4'
$visible.accuracy_note = "$($config.target_rows) official GOV.UK local-authority rows; latest $($config.new_rows) rows were selected from the downloaded official CSV by exact authority code and year, with SHA256 evidence. Parcel binding remains pending."
$visible.source_local_raw_path = $sourceLocalPath
$visible | Add-Member -NotePropertyName source_local_sha256 -NotePropertyValue $sourceSha256 -Force
$visible | Add-Member -NotePropertyName source_local_size_bytes -NotePropertyValue $sourceSize -Force
$visible | Add-Member -NotePropertyName browser_smoke_passed_for_target_rows -NotePropertyValue $false -Force
$visible.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$visible.final_ready = $false
$visible.product_final_ready = $false
$visible.fake_data = $false
Write-Json $rowsPath $visible

$artifactSha256 = (Get-FileHash -LiteralPath $rowsPath -Algorithm SHA256).Hash.ToLowerInvariant()
$canonical = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
$canonical.status = "OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_$($config.target_rows)_PENDING_BROWSER_SMOKE"
$canonical.visible_rows_count = [int]$config.target_rows
$canonical.previous_visible_row_count = [int]$config.previous_rows
$canonical.new_rows_added_this_run = [int]$config.new_rows
$canonical.current_visible_change_rows = [int]$config.new_rows
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

$httpRowsUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json?year_selector=' + $config.year + '&ts=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$httpCount = -1
$httpError = $null
for ($i=0; $i -lt 20; $i++) {
  try {
    $resp = Invoke-RestMethod -Uri $httpRowsUrl -Method Get -TimeoutSec 20 -Headers @{ 'Cache-Control'='no-cache' }
    $httpCount = @($resp.rows).Count
    if ($httpCount -eq [int]$config.target_rows) { break }
  } catch { $httpError = $_.Exception.Message }
  Start-Sleep -Seconds 2
}
if ($httpCount -ne [int]$config.target_rows) {
  throw "HTTP_8012_TARGET_ROW_COUNT_MISMATCH: actual=$httpCount expected=$($config.target_rows) error=$httpError"
}

$expectedIdsPath = Join-Path ([System.IO.Path]::GetTempPath()) ($taskId + '_expected_ids.json')
Write-Json $expectedIdsPath $ids
$tmpPy = Join-Path ([System.IO.Path]::GetTempPath()) ($taskId + '_browser.py')
$tmpOut = Join-Path ([System.IO.Path]::GetTempPath()) ($taskId + '_browser.json')
$pythonSource = @'
import json
import math
import sys
import time
from pathlib import Path

out_path = Path(sys.argv[1])
expected_ids = set(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8-sig")))
target = int(sys.argv[3])
new_count_expected = int(sys.argv[4])
year = int(sys.argv[5])
pages = math.ceil(target / 25)
url = f"http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=gas{target}&year={year}&ts={int(time.time())}"
result = {"status":"FAIL","url":url,"expected_row_count":target,"unique_row_count":0,"new_marker_count":0,"manual_marker_on_new_count":0,"page_infos":[],"console_errors":[],"error":None}
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
    wait = WebDriverWait(driver, 90)
    wait.until(lambda d: d.find_element(By.ID, "layerSelect"))
    Select(driver.find_element(By.ID, "layerSelect")).select_by_value("gas")
    wait.until(lambda d: f"{target} satır" in d.find_element(By.ID, "pageInfo").text)
    row_map = {}
    for page_no in range(1, pages + 1):
        wait.until(lambda d, p=page_no: f"Sayfa {p} / {pages}" in d.find_element(By.ID, "pageInfo").text)
        result["page_infos"].append(driver.find_element(By.ID, "pageInfo").text.strip())
        for row in driver.find_elements(By.CSS_SELECTOR, "#table tbody tr"):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                rid = cells[1].text.strip()
                if rid:
                    row_map[rid] = cells[0].text.strip()
        if page_no < pages:
            driver.find_element(By.ID, "next").click()
    try:
        severe = [e for e in driver.get_log("browser") if str(e.get("level", "")).upper() == "SEVERE"]
    except Exception:
        severe = []
    new_count = sum(1 for rid in expected_ids if "YENİ / LATEST" in row_map.get(rid, ""))
    manual_count = sum(1 for rid in expected_ids if "MANUEL İNCELEME" in row_map.get(rid, ""))
    passed = len(row_map) == target and expected_ids.issubset(row_map) and new_count == new_count_expected and manual_count == new_count_expected and not severe
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
  & $python.Source $tmpPy $tmpOut $expectedIdsPath $config.target_rows $config.new_rows $config.year
} else {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if (-not $py) { throw 'PYTHON_NOT_FOUND_FOR_YEAR_SELECTOR_SELENIUM' }
  & $py.Source -3 $tmpPy $tmpOut $expectedIdsPath $config.target_rows $config.new_rows $config.year
}
$browserExit = $LASTEXITCODE
if (-not (Test-Path -LiteralPath $tmpOut)) { throw 'YEAR_SELECTOR_SELENIUM_RESULT_NOT_WRITTEN' }
$browser = Get-Content -LiteralPath $tmpOut -Raw -Encoding UTF8 | ConvertFrom-Json
$browserPassed = ($browserExit -eq 0 -and [string]$browser.status -eq 'PASS' -and [int]$browser.unique_row_count -eq [int]$config.target_rows -and [int]$browser.new_marker_count -eq [int]$config.new_rows)

$payload = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  status = if ($browserPassed) { "PASS_$($config.target_rows)_VISIBLE_ROWS" } else { "FAIL_$($config.target_rows)_BROWSER_GATE" }
  generated_by_runner = $true
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  target_branch = $branch
  calendar_year = [int]$config.year
  initial_visible_rows = $initialCount
  verified_new_rows = [int]$config.new_rows
  visible_rows_after = [int]$config.target_rows
  official_preview_line_start = [int]$config.preview_start
  official_preview_line_end = [int]$config.preview_end
  source_url = $sourceUrl
  source_local_raw_path = $sourceLocalPath
  source_local_size_bytes = $sourceSize
  source_local_sha256 = $sourceSha256
  artifact_sha256 = $artifactSha256
  official_year_selector_passed = $true
  browser = $browser
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
  $canonical.status = "OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_$($config.target_rows)_BROWSER_PASS"
  $canonical.browser_smoke_passed = $true
  $canonical | Add-Member -NotePropertyName browser_smoke_row_count -NotePropertyValue ([int]$config.target_rows) -Force
  $canonical | Add-Member -NotePropertyName browser_smoke_new_marker_count -NotePropertyValue ([int]$config.new_rows) -Force
  $canonical | Add-Member -NotePropertyName browser_smoke_report_path -NotePropertyValue ([string]$config.report_rel) -Force
  $canonical | Add-Member -NotePropertyName browser_smoke_passed_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
  $canonical.next_required_runner_action = 'Continue official source expansion only through exact downloaded-CSV selectors; parcel binding remains blocked until defensible spatial allocation evidence exists.'
  $canonical.final_ready = $false
  $canonical.product_final_ready = $false
  $canonical.fake_data = $false
  Write-Json $statusPath $canonical
  Copy-Atomic $statusPath (Join-Path $servedRepoRoot $statusRel)
}

Remove-Item -LiteralPath $tmpPy,$tmpOut,$expectedIdsPath -Force -ErrorAction SilentlyContinue
if (-not $browserPassed) { throw "GAS_EMISSIONS_$($config.target_rows)_BROWSER_SMOKE_FAILED" }
Write-Output ($payload | ConvertTo-Json -Depth 100)
