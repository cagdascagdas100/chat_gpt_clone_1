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

function Copy-Atomic([string]$Source,[string]$Target) {
  $sourceFull = [System.IO.Path]::GetFullPath($Source)
  $targetFull = [System.IO.Path]::GetFullPath($Target)
  if ($sourceFull -eq $targetFull) { return }
  Ensure-Dir (Split-Path -Parent $targetFull)
  $tmp = $targetFull + '.aays_tmp_' + [Guid]::NewGuid().ToString('N')
  Copy-Item -LiteralPath $sourceFull -Destination $tmp -Force
  Move-Item -LiteralPath $tmp -Destination $targetFull -Force
}

function Get-RowCount([string]$Path) {
  $obj = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
  return @($obj.rows).Count
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$taskId = [string]$env:AAYS_TASK_ID
$pageKey = [string]$env:AAYS_PAGE_KEY
$branch = [string]$env:AAYS_TARGET_BRANCH
$controllerRoot = [string]$env:AAYS_CONTROLLER_REPO_ROOT

if (-not $repoRoot -or -not $taskId -or $pageKey -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_STANDALONE_PROOF_WRONG_CONTEXT'
}
if ($branch -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_STANDALONE_PROOF_WRONG_BRANCH'
}
if (-not $controllerRoot -and $env:AAYS_PORTABLE_ROOT) {
  $controllerRoot = Join-Path ([string]$env:AAYS_PORTABLE_ROOT) 'runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
}
if (-not $controllerRoot) { $controllerRoot = $repoRoot }
if (-not (Test-Path -LiteralPath $controllerRoot)) {
  throw "GAS_EMISSIONS_STANDALONE_CONTROLLER_NOT_FOUND: $controllerRoot"
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

$publishRels = @($rowsRel,$statusRel,$matrixRel)
foreach ($extra in @(
  'england_map_web\data\program_layer_matrix\gas_emissions_source_manifest_latest.json',
  'england_map_web\data\program_layer_matrix\gas_emissions_row_evidence_latest.json',
  'england_map_web\data\program_layer_matrix\gas_emissions_pipeline_latest.json'
)) {
  if (Test-Path -LiteralPath (Join-Path $repoRoot $extra)) { $publishRels += $extra }
}
foreach ($rel in $publishRels) {
  Copy-Atomic (Join-Path $repoRoot $rel) (Join-Path $controllerRoot $rel)
}

$servedRowsPath = Join-Path $controllerRoot $rowsRel
$servedLocalCount = Get-RowCount $servedRowsPath
if ($servedLocalCount -ne $ExpectedRows) {
  throw "SERVED_LOCAL_ROW_COUNT_MISMATCH: actual=$servedLocalCount expected=$ExpectedRows"
}

$httpUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json?standalone=' + $ExpectedRows + '&ts=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
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

$tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('gas_standalone_proof_' + $taskId)
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
url = f"http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=gas{target}&standalone=1&ts={int(time.time())}"
result = {
    "status":"FAIL", "url":url, "expected_row_count":target, "unique_row_count":0,
    "new_marker_count":0, "manual_marker_on_new_count":0, "page_infos":[],
    "required_headers_present":False, "headers":[], "console_errors":[], "error":None,
    "load_attempts":[]
}
driver = None
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import TimeoutException

    options = webdriver.ChromeOptions()
    options.page_load_strategy = "eager"
    for arg in ("--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1920,1400", "--no-proxy-server", "--proxy-bypass-list=<-loopback>"):
        options.add_argument(arg)
    options.set_capability("goog:loggingPrefs", {"browser":"ALL"})
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(90)
    driver.set_script_timeout(180)
    try:
        driver.get(url)
    except TimeoutException:
        pass

    wait = WebDriverWait(driver, 120)
    wait.until(lambda d: d.execute_script("return document.readyState") in ("interactive", "complete"))
    wait.until(lambda d: len(d.find_elements(By.ID, "layerSelect")) == 1)
    wait.until(lambda d: d.execute_script("return typeof loadLayer") == "function")
    try:
        WebDriverWait(driver, 35).until(lambda d: len(d.find_elements(By.ID, "message")) == 1 and "Veri yükleniyor" not in d.find_element(By.ID, "message").text)
    except Exception:
        pass

    loaded = False
    for attempt in range(1, 4):
        async_result = driver.execute_async_script("""
          const done = arguments[arguments.length - 1];
          (async () => {
            const select = document.getElementById('layerSelect');
            if (!select) throw new Error('layerSelect_missing');
            if (typeof loadLayer !== 'function') throw new Error('loadLayer_missing');
            select.value = 'gas';
            await loadLayer('gas');
            select.value = 'gas';
            return {ok:true, pageInfo:(document.getElementById('pageInfo')||{}).textContent||'', message:(document.getElementById('message')||{}).textContent||''};
          })().then(v => done(v)).catch(e => done({ok:false,error:String(e)}));
        """)
        result["load_attempts"].append(async_result)
        try:
            WebDriverWait(driver, 75).until(
                lambda d: d.find_element(By.ID, "layerSelect").get_attribute("value") == "gas"
                and str(target) in d.find_element(By.ID, "pageInfo").text
                and "Sayfa" in d.find_element(By.ID, "pageInfo").text
                and len(d.find_elements(By.CSS_SELECTOR, "#table tbody tr")) > 0
            )
            loaded = True
            break
        except Exception:
            time.sleep(2)
    if not loaded:
        raise RuntimeError("gas_layer_did_not_render_target_rows")

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
                    rows[rid] = {
                        "status_text": cells[0].text.strip(),
                        "classes": (tr.get_attribute("class") or "").split()
                    }
        m = re.search(r"Sayfa\s+(\d+)\s*/\s*(\d+)", info)
        if not m or int(m.group(1)) >= int(m.group(2)):
            break
        next_page = int(m.group(1)) + 1
        driver.find_element(By.ID, "next").click()
        WebDriverWait(driver, 45).until(lambda d, p=next_page: re.search(rf"Sayfa\s+{p}\s*/", d.find_element(By.ID, "pageInfo").text))

    headers = [x.text.strip() for x in driver.find_elements(By.CSS_SELECTOR, "#table thead th")]
    required_headers = {"Hesap a\u00e7\u0131klamas\u0131","Parcel binding","Ham yerel kaynak","Visible artifact","Status yolu","Rapor yolu","Served commit","Artifact SHA"}
    import unicodedata
    def norm_text(value):
        return " ".join(unicodedata.normalize("NFC", str(value)).split())
    headers_norm = {norm_text(x) for x in headers}
    required_headers_norm = {norm_text(x) for x in required_headers}
    missing_required_headers = sorted(required_headers_norm - headers_norm)
    try:
        severe = [e for e in driver.get_log("browser") if str(e.get("level", "")).upper() == "SEVERE"]
    except Exception:
        severe = []
    new_count = sum("YENİ / LATEST" in rows.get(rid, "") for rid in expected_ids)
    manual_count = sum("MANUEL İNCELEME" in rows.get(rid, "") for rid in expected_ids)
    new_count = sum("latest" in rows.get(rid, {}).get("classes", []) for rid in expected_ids)
    manual_count = sum("manual" in rows.get(rid, {}).get("classes", []) for rid in expected_ids)
    passed = (
        len(rows) == target and expected_ids.issubset(rows) and
        new_count == expected_latest and manual_count == expected_latest and
        not missing_required_headers and not severe
    )
    result.update({
        "status":"PASS" if passed else "FAIL", "unique_row_count":len(rows),
        "new_marker_count":new_count, "manual_marker_on_new_count":manual_count,
        "expected_latest_rows_present":expected_ids.issubset(rows),
        "headers":headers, "required_headers_present":not missing_required_headers,
        "missing_required_headers":missing_required_headers,
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
$actualBrowserRows = [int]$browser.unique_row_count

$reportRel = "docs/chatgpt_status/gas_emissions/reports/182_gas_emissions_${ExpectedRows}_standalone_browser_proof_20260713.json"
$resultStatusRel = "docs/chatgpt_status/gas_emissions/status/182_gas_emissions_${ExpectedRows}_standalone_browser_proof_latest.json"
$reportPath = Join-Path $repoRoot ($reportRel -replace '/','\')
$resultStatusPath = Join-Path $repoRoot ($resultStatusRel -replace '/','\')

$status = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
$statusLabel = if ($browserPassed) {
  "OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_$ExpectedRows"
} else {
  "OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_${ExpectedRows}_BROWSER_BLOCKED"
}
$status | Add-Member -NotePropertyName status -NotePropertyValue $statusLabel -Force
$status | Add-Member -NotePropertyName browser_smoke_passed -NotePropertyValue $browserPassed -Force
$status | Add-Member -NotePropertyName browser_smoke_row_count -NotePropertyValue $actualBrowserRows -Force
$status | Add-Member -NotePropertyName browser_smoke_new_marker_count -NotePropertyValue ([int]$browser.new_marker_count) -Force
$status | Add-Member -NotePropertyName browser_smoke_manual_marker_count -NotePropertyValue ([int]$browser.manual_marker_on_new_count) -Force
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

$payloadStatus = if ($browserPassed) {
  'PASS_STANDALONE_LIVE_PUBLISH_AND_BROWSER_PROOF'
} else {
  'FAIL_STANDALONE_BROWSER_PROOF'
}
$payload = [ordered]@{
  task_id=$taskId
  page_key='gas_emissions'
  status=$payloadStatus
  generated_at=(Get-Date).ToUniversalTime().ToString('o')
  expected_rows=$ExpectedRows
  canonical_rows=$canonicalCount
  served_local_rows=$servedLocalCount
  served_http_rows=$httpCount
  latest_rows=$latestCount
  browser=$browser
  browser_smoke_passed=$browserPassed
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
if (-not $browserPassed) { throw 'GAS_EMISSIONS_STANDALONE_BROWSER_PROOF_FAILED' }
Write-Output ($payload | ConvertTo-Json -Depth 100)
