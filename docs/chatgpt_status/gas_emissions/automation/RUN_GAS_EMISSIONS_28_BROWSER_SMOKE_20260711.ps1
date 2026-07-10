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
    (($Value | ConvertTo-Json -Depth 50) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$taskId = [string]$env:AAYS_TASK_ID
$pageKey = [string]$env:AAYS_PAGE_KEY
$branch = [string]$env:AAYS_TARGET_BRANCH

if (-not $repoRoot -or -not $taskId -or $pageKey -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_SMOKE_MUST_RUN_INSIDE_CANONICAL_SHARED_RUNNER'
}

$reportRel = 'docs/chatgpt_status/gas_emissions/reports/149_gas_emissions_browser_smoke_28_20260711.json'
$statusRel = 'docs/chatgpt_status/gas_emissions/status/149_gas_emissions_browser_smoke_28_20260711_latest.json'
$canonicalStatusRel = 'england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
$reportPath = Join-Path $repoRoot ($reportRel -replace '/', '\')
$statusPath = Join-Path $repoRoot ($statusRel -replace '/', '\')
$canonicalStatusPath = Join-Path $repoRoot ($canonicalStatusRel -replace '/', '\')

$tmpBase = Join-Path ([System.IO.Path]::GetTempPath()) $taskId
$tmpPy = $tmpBase + '.py'
$tmpOut = $tmpBase + '.json'

$pythonSource = @'
import json
import sys
import time
from pathlib import Path

out_path = Path(sys.argv[1])
url = "http://127.0.0.1:8012/england_map_web/index.html?gas_smoke=28&ts=" + str(int(time.time()))
expected_ids = {
    "GHG-HPL-2005-waste-other-n2o",
    "GHG-HPL-2006-agriculture-gas-ch4",
    "GHG-HPL-2006-agriculture-gas-n2o",
    "GHG-HPL-2006-commercial-electricity-n2o",
}
result = {
    "status": "FAIL",
    "browser": "Google Chrome via Selenium",
    "url": url,
    "expected_row_count": 28,
    "rendered_row_count": 0,
    "expected_new_rows_present": False,
    "rows_summary": "",
    "title": "",
    "console_errors": [],
    "error": None,
}

driver = None
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1600,1200")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    wait = WebDriverWait(driver, 40)
    wait.until(lambda d: "official GOV.UK visible rows loaded" in d.find_element(By.ID, "rowsSummary").text)
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#rowsTable tbody tr")) >= 28)

    rows = driver.find_elements(By.CSS_SELECTOR, "#rowsTable tbody tr")
    row_ids = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if cells:
            row_ids.append(cells[0].text.strip())

    summary = driver.find_element(By.ID, "rowsSummary").text.strip()
    severe_logs = []
    try:
        severe_logs = [entry for entry in driver.get_log("browser") if str(entry.get("level", "")).upper() == "SEVERE"]
    except Exception:
        severe_logs = []

    rendered = len(rows)
    expected_present = expected_ids.issubset(set(row_ids))
    passed = rendered == 28 and expected_present and summary.startswith("28 official GOV.UK visible rows loaded") and not severe_logs

    result.update({
        "status": "PASS" if passed else "FAIL",
        "rendered_row_count": rendered,
        "expected_new_rows_present": expected_present,
        "expected_new_row_ids": sorted(expected_ids),
        "rendered_row_ids": row_ids,
        "rows_summary": summary,
        "title": driver.title,
        "console_errors": severe_logs,
    })
    if not passed:
        result["error"] = "row_count_summary_expected_ids_or_console_check_failed"
except Exception as exc:
    result["error"] = f"{type(exc).__name__}: {exc}"
finally:
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

sys.exit(0 if result["status"] == "PASS" else 1)
'@

[System.IO.File]::WriteAllText($tmpPy, $pythonSource, [System.Text.UTF8Encoding]::new($false))
$python = Get-Command python -ErrorAction SilentlyContinue
$exitCode = 1
if ($python) {
  & $python.Source $tmpPy $tmpOut
  $exitCode = $LASTEXITCODE
} else {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if (-not $py) { throw 'PYTHON_NOT_FOUND_FOR_SELENIUM_SMOKE' }
  & $py.Source -3 $tmpPy $tmpOut
  $exitCode = $LASTEXITCODE
}

if (-not (Test-Path -LiteralPath $tmpOut)) {
  throw 'SELENIUM_RESULT_NOT_WRITTEN'
}
$result = Get-Content -LiteralPath $tmpOut -Raw -Encoding UTF8 | ConvertFrom-Json
$passed = ($exitCode -eq 0 -and [string]$result.status -eq 'PASS' -and [int]$result.rendered_row_count -eq 28)

$payload = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  target_branch = $branch
  status = if ($passed) { 'PASS' } else { 'FAIL' }
  generated_by_runner = $true
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  browser = $result.browser
  url = $result.url
  expected_row_count = 28
  rendered_row_count = [int]$result.rendered_row_count
  expected_new_rows_present = [bool]$result.expected_new_rows_present
  expected_new_row_ids = @($result.expected_new_row_ids)
  rows_summary = [string]$result.rows_summary
  title = [string]$result.title
  console_errors = @($result.console_errors)
  error = $result.error
  source_rows_path = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
  canonical_status_path = $canonicalStatusRel
  single_runner_only = $true
  new_runner = $false
  parallel_runner = $false
  parcel_binding_gate_passed = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json $reportPath $payload
Write-Json $statusPath $payload

if ($passed) {
  $canonical = Get-Content -LiteralPath $canonicalStatusPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $canonical.browser_smoke_passed = $true
  $canonical | Add-Member -NotePropertyName browser_smoke_row_count -NotePropertyValue 28 -Force
  $canonical | Add-Member -NotePropertyName browser_smoke_report_path -NotePropertyValue $reportRel -Force
  $canonical | Add-Member -NotePropertyName browser_smoke_passed_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
  $canonical.next_required_runner_action = 'Continue official GOV.UK source expansion in small batches, then begin parcel-level matching without inventing geometry or allocation.'
  $canonical.final_ready = $false
  $canonical.product_final_ready = $false
  $canonical.fake_data = $false
  Write-Json $canonicalStatusPath $canonical
}

Remove-Item -LiteralPath $tmpPy,$tmpOut -Force -ErrorAction SilentlyContinue

if (-not $passed) {
  throw 'GAS_EMISSIONS_28_BROWSER_SMOKE_FAILED'
}

Write-Output ($payload | ConvertTo-Json -Depth 50)
