[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][int]$ExpectedRows
)

$ErrorActionPreference = 'Stop'

function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Write-Json([string]$Path,[object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText(
    $Path,
    (($Value | ConvertTo-Json -Depth 100) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
}

function Get-RowCount([string]$Path) {
  $o = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
  return @($o.rows).Count
}

function Copy-Atomic([string]$Source,[string]$Target) {
  Ensure-Dir (Split-Path -Parent $Target)
  $tmp = $Target + '.aays_tmp_' + [Guid]::NewGuid().ToString('N')
  Copy-Item -LiteralPath $Source -Destination $tmp -Force
  Move-Item -LiteralPath $tmp -Destination $Target -Force
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$taskId = [string]$env:AAYS_TASK_ID
$pageKey = [string]$env:AAYS_PAGE_KEY
$branch = [string]$env:AAYS_TARGET_BRANCH
$controllerRoot = [string]$env:AAYS_CONTROLLER_REPO_ROOT

if (-not $repoRoot -or -not $taskId -or $pageKey -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_GENERIC_PUBLISH_MUST_RUN_INSIDE_CANONICAL_SHARED_RUNNER'
}
if ($branch -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_GENERIC_PUBLISH_WRONG_BRANCH'
}
if (-not $controllerRoot -or -not (Test-Path -LiteralPath $controllerRoot)) {
  throw 'AAYS_CONTROLLER_REPO_ROOT_MISSING_OR_NOT_FOUND'
}

$rowsRel = 'england_map_web\data\program_layer_matrix\gas_emissions_visible_rows_latest.json'
$statusRel = 'england_map_web\data\program_layer_matrix\gas_emissions_status_latest.json'
$matrixRel = 'england_map_web\TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$rowsPath = Join-Path $repoRoot $rowsRel
$statusPath = Join-Path $repoRoot $statusRel
$matrixPath = Join-Path $repoRoot $matrixRel
foreach ($required in @($rowsPath,$statusPath,$matrixPath)) {
  if (-not (Test-Path -LiteralPath $required)) { throw "MISSING_REQUIRED_FILE: $required" }
}

$visible = Get-Content -LiteralPath $rowsPath -Raw -Encoding UTF8 | ConvertFrom-Json
$canonicalCount = @($visible.rows).Count
if ($canonicalCount -ne $ExpectedRows) {
  throw "CANONICAL_ROW_COUNT_MISMATCH: actual=$canonicalCount expected=$ExpectedRows"
}

$allIds = [string[]]@($visible.rows | ForEach-Object { [string]$_.row_id })
$uniqueIds = @($allIds | Select-Object -Unique)
if ($uniqueIds.Count -ne $ExpectedRows) {
  throw "CANONICAL_DUPLICATE_ROW_IDS: unique=$($uniqueIds.Count) expected=$ExpectedRows"
}
$latestIds = [string[]]@($visible.rows | Where-Object { $_.is_new_in_latest_batch -eq $true } | ForEach-Object { [string]$_.row_id })
$latestCount = @($latestIds).Count
if ($latestCount -le 0) { throw 'LATEST_BATCH_IDS_NOT_FOUND' }

$publisher = Join-Path $repoRoot 'docs\chatgpt_status\_shared\automation\PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1'
$publishRels = @($rowsRel,$statusRel,$matrixRel)
foreach ($extra in @(
  'england_map_web\data\program_layer_matrix\gas_emissions_source_manifest_latest.json',
  'england_map_web\data\program_layer_matrix\gas_emissions_row_evidence_latest.json',
  'england_map_web\data\program_layer_matrix\gas_emissions_pipeline_latest.json'
)) {
  if (Test-Path -LiteralPath (Join-Path $repoRoot $extra)) { $publishRels += $extra }
}

$publisherStatus = 'not_available'
if (Test-Path -LiteralPath $publisher) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $repoRoot -ControllerRoot $controllerRoot -Paths ($publishRels -join '|') -AllowGeneratedArtifacts -SyncPortableWeb
  if ($LASTEXITCODE -ne 0) { throw 'GENERIC_LIVE_CONTROLLER_PUBLISH_FAILED' }
  $publisherStatus = 'PASS'
}

foreach ($rel in @($rowsRel,$statusRel,$matrixRel)) {
  $source = Join-Path $repoRoot $rel
  $target = Join-Path $controllerRoot $rel
  $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
  $targetHash = if (Test-Path -LiteralPath $target) { (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash } else { '' }
  if ($sourceHash -ne $targetHash) { Copy-Atomic $source $target }
}

$servedRowsPath = Join-Path $controllerRoot $rowsRel
$servedLocalCount = Get-RowCount $servedRowsPath
if ($servedLocalCount -ne $ExpectedRows) {
  throw "SERVED_LOCAL_ROW_COUNT_MISMATCH: actual=$servedLocalCount expected=$ExpectedRows"
}

$httpUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json?generic_publish=' + $ExpectedRows + '&ts=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$httpCount = -1
$httpError = $null
for ($i=0; $i -lt 20; $i++) {
  try {
    $resp = Invoke-RestMethod -Uri $httpUrl -Method Get -TimeoutSec 20 -Headers @{ 'Cache-Control'='no-cache' }
    $httpCount = @($resp.rows).Count
    if ($httpCount -eq $ExpectedRows) { break }
  } catch { $httpError = $_.Exception.Message }
  Start-Sleep -Seconds 2
}
if ($httpCount -ne $ExpectedRows) {
  throw "HTTP_8012_ROW_COUNT_MISMATCH: actual=$httpCount expected=$ExpectedRows error=$httpError"
}

$tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('gas_generic_proof_' + $taskId)
$tmpExpected = $tmpRoot + '.expected.json'
$tmpPy = $tmpRoot + '.py'
$tmpOut = $tmpRoot + '.result.json'
Write-Json -Path $tmpExpected -Value ([object[]]@($latestIds))

$pythonSource = @'
import json, math, re, sys, time
from pathlib import Path

out_path = Path(sys.argv[1])
expected_ids = set(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8-sig")))
target = int(sys.argv[3])
expected_latest = int(sys.argv[4])
url = f"http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=gas{target}&generic=1&ts={int(time.time())}"
result = {
    "status":"FAIL", "url":url, "expected_row_count":target, "unique_row_count":0,
    "new_marker_count":0, "manual_marker_on_new_count":0, "page_infos":[],
    "required_headers_present":False, "headers":[], "console_errors":[], "error":None,
}
driver = None
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    options = webdriver.ChromeOptions()
    for arg in ("--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1920,1400"):
        options.add_argument(arg)
    options.set_capability("goog:loggingPrefs", {"browser":"ALL"})
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    wait = WebDriverWait(driver, 90)
    wait.until(lambda d: d.find_element(By.ID, "layerSelect"))
    Select(driver.find_element(By.ID, "layerSelect")).select_by_value("gas")
    wait.until(lambda d: f"{target} satır" in d.find_element(By.ID, "pageInfo").text)
    rows = {}
    max_pages = max(1, math.ceil(target / 25))
    for _ in range(max_pages + 2):
        info = driver.find_element(By.ID, "pageInfo").text.strip()
        result["page_infos"].append(info)
        for tr in driver.find_elements(By.CSS_SELECTOR, "#table tbody tr"):
            cells = tr.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                rid = cells[1].text.strip()
                if rid:
                    rows[rid] = cells[0].text.strip()
        m = re.search(r"Sayfa\s+(\d+)\s*/\s*(\d+)", info)
        if not m or int(m.group(1)) >= int(m.group(2)):
            break
        next_page = int(m.group(1)) + 1
        driver.find_element(By.ID, "next").click()
        wait.until(lambda d, p=next_page: re.search(rf"Sayfa\s+{p}\s*/", d.find_element(By.ID, "pageInfo").text))
    headers = [x.text.strip() for x in driver.find_elements(By.CSS_SELECTOR, "#table thead th")]
    required_headers = {"Hesap açıklaması","Parcel binding","Ham yerel kaynak","Visible artifact","Status yolu","Rapor yolu","Served commit","Artifact SHA"}
    try:
        severe = [e for e in driver.get_log("browser") if str(e.get("level", "")).upper() == "SEVERE"]
    except Exception:
        severe = []
    new_count = sum("YENİ / LATEST" in rows.get(rid, "") for rid in expected_ids)
    manual_count = sum("MANUEL İNCELEME" in rows.get(rid, "") for rid in expected_ids)
    passed = (
        len(rows) == target and expected_ids.issubset(rows) and
        new_count == expected_latest and manual_count == expected_latest and
        required_headers.issubset(set(headers)) and not severe
    )
    result.update({
        "status":"PASS" if passed else "FAIL", "unique_row_count":len(rows),
        "new_marker_count":new_count, "manual_marker_on_new_count":manual_count,
        "expected_latest_rows_present":expected_ids.issubset(rows),
        "headers":headers, "required_headers_present":required_headers.issubset(set(headers)),
        "console_errors":severe, "title":driver.title,
    })
    if not passed:
        result["error"] = "count_ids_markers_headers_or_console_check_failed"
except Exception as exc:
    result["error"] = f"{type(exc).__name__}: {exc}"
finally:
    if driver is not None:
        try: driver.quit()
        except Exception: pass
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
sys.exit(0 if result["status"] == "PASS" else 1)
'@

[System.IO.File]::WriteAllText($tmpPy,$pythonSource,[System.Text.UTF8Encoding]::new($false))
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
  & $python.Source $tmpPy $tmpOut $tmpExpected $ExpectedRows $latestCount
} else {
  $py = Get-Command py -ErrorAction Stop
  & $py.Source -3 $tmpPy $tmpOut $tmpExpected $ExpectedRows $latestCount
}
$browserExit = $LASTEXITCODE
$browser = Get-Content -LiteralPath $tmpOut -Raw -Encoding UTF8 | ConvertFrom-Json
$browserPassed = ($browserExit -eq 0 -and [string]$browser.status -eq 'PASS' -and [int]$browser.unique_row_count -eq $ExpectedRows)

$reportRel = "docs/chatgpt_status/gas_emissions/reports/177_gas_emissions_${ExpectedRows}_live_publish_browser_repair_20260713.json"
$resultStatusRel = "docs/chatgpt_status/gas_emissions/status/177_gas_emissions_${ExpectedRows}_live_publish_browser_repair_latest.json"
$reportPath = Join-Path $repoRoot ($reportRel -replace '/','\')
$resultStatusPath = Join-Path $repoRoot ($resultStatusRel -replace '/','\')

$status = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
$status | Add-Member -NotePropertyName status -NotePropertyValue ("OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_" + $ExpectedRows) -Force
$status | Add-Member -NotePropertyName browser_smoke_passed -NotePropertyValue $browserPassed -Force
$status | Add-Member -NotePropertyName browser_smoke_row_count -NotePropertyValue $ExpectedRows -Force
$status | Add-Member -NotePropertyName browser_smoke_new_marker_count -NotePropertyValue $latestCount -Force
$status | Add-Member -NotePropertyName browser_smoke_manual_marker_count -NotePropertyValue $latestCount -Force
$status | Add-Member -NotePropertyName browser_smoke_report_path -NotePropertyValue $reportRel -Force
$status | Add-Member -NotePropertyName browser_smoke_passed_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
$status | Add-Member -NotePropertyName served_publish_root -NotePropertyValue $controllerRoot -Force
$status | Add-Member -NotePropertyName parcel_binding_gate_passed -NotePropertyValue $false -Force
$status | Add-Member -NotePropertyName final_ready -NotePropertyValue $false -Force
$status | Add-Member -NotePropertyName product_final_ready -NotePropertyValue $false -Force
$status | Add-Member -NotePropertyName fake_data -NotePropertyValue $false -Force
$status | Add-Member -NotePropertyName db_write -NotePropertyValue $false -Force
$status | Add-Member -NotePropertyName migration -NotePropertyValue $false -Force
$status | Add-Member -NotePropertyName production_deploy -NotePropertyValue $false -Force
Write-Json $statusPath $status
Copy-Atomic $statusPath (Join-Path $controllerRoot $statusRel)

$payload = [ordered]@{
  task_id=$taskId
  page_key='gas_emissions'
  status=if($browserPassed){'PASS_LIVE_PUBLISH_AND_BROWSER_PROOF'}else{'FAIL_BROWSER_PROOF'}
  generated_at=(Get-Date).ToUniversalTime().ToString('o')
  expected_rows=$ExpectedRows
  canonical_rows=$canonicalCount
  served_local_rows=$servedLocalCount
  served_http_rows=$httpCount
  latest_rows=$latestCount
  browser=$browser
  browser_smoke_passed=$browserPassed
  publisher_status=$publisherStatus
  controller_root=$controllerRoot
  report_path=$reportRel
  result_status_path=$resultStatusRel
  single_runner_only=$true
  new_runner=$false
  parallel_runner=$false
  parcel_binding_gate_passed=$false
  final_ready=$false
  product_final_ready=$false
  fake_data=$false
  db_write=$false
  migration=$false
  production_deploy=$false
}
Write-Json $reportPath $payload
Write-Json $resultStatusPath $payload

Remove-Item -LiteralPath $tmpPy,$tmpExpected,$tmpOut -Force -ErrorAction SilentlyContinue
if (-not $browserPassed) { throw 'GENERIC_GAS_EMISSIONS_BROWSER_PROOF_FAILED' }
Write-Output ($payload | ConvertTo-Json -Depth 100)
