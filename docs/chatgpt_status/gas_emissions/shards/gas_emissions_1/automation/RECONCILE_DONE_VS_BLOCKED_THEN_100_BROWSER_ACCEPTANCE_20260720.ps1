[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Ensure-Directory([string]$Path) {
    if ($Path -and -not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Write-Json([string]$Path, [object]$Value) {
    Ensure-Directory (Split-Path -Parent $Path)
    [System.IO.File]::WriteAllText(
        $Path,
        (($Value | ConvertTo-Json -Depth 100) + "`n"),
        [System.Text.UTF8Encoding]::new($false)
    )
}

function Read-Json([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

$repoRoot = [System.IO.Path]::GetFullPath((Get-Location).Path)
$slotId = [string]$env:AAYS_SLOT_ID
$taskId = [string]$env:AAYS_TASK_ID
if ($slotId -ne 'gas_emissions_1') { throw "WRONG_SLOT: $slotId" }
if (-not $taskId) { throw 'AAYS_TASK_ID_MISSING' }
if ([string]$env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN -ne 'true') { throw 'CHILD_DIRECT_PUSH_GUARD_MISSING' }

$rowsRel = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
$statusRel = 'england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
$matrixRel = 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$proof37Rel = 'docs/chatgpt_status/gas_emissions/reports/176_gas_emissions_37_browser_proof_latest.json'
$proof66Rel = 'docs/chatgpt_status/gas_emissions/reports/182_gas_emissions_66_standalone_browser_proof_20260713.json'
$outputRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_reconcile_100_browser_acceptance_latest.json'
$statusOutputRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_browser_acceptance_latest.json'

$rowsPath = Join-Path $repoRoot ($rowsRel -replace '/', '\')
$statusPath = Join-Path $repoRoot ($statusRel -replace '/', '\')
$matrixPath = Join-Path $repoRoot ($matrixRel -replace '/', '\')
$outputPath = Join-Path $repoRoot ($outputRel -replace '/', '\')
$statusOutputPath = Join-Path $repoRoot ($statusOutputRel -replace '/', '\')

$blockers = [System.Collections.Generic.List[string]]::new()
foreach ($required in @($rowsPath, $statusPath, $matrixPath)) {
    if (-not (Test-Path -LiteralPath $required)) {
        $blockers.Add("MISSING_REQUIRED_FILE:$required")
    }
}

$rows = Read-Json $rowsPath
$layerStatus = Read-Json $statusPath
$proof37 = Read-Json (Join-Path $repoRoot ($proof37Rel -replace '/', '\'))
$proof66 = Read-Json (Join-Path $repoRoot ($proof66Rel -replace '/', '\'))

$canonicalRows = if ($rows) { @($rows.rows).Count } else { -1 }
$uniqueIds = if ($rows) { @($rows.rows | ForEach-Object { [string]$_.row_id } | Select-Object -Unique).Count } else { -1 }
$latestIds = if ($rows) { [string[]]@($rows.rows | Where-Object { $_.is_new_in_latest_batch -eq $true } | ForEach-Object { [string]$_.row_id }) } else { [string[]]@() }
$latestCount = @($latestIds).Count
$declaredVisibleRows = if ($layerStatus -and $null -ne $layerStatus.visible_rows_count) { [int]$layerStatus.visible_rows_count } else { -1 }
$declaredBrowserRows = if ($layerStatus -and $null -ne $layerStatus.browser_smoke_row_count) { [int]$layerStatus.browser_smoke_row_count } else { -1 }
$declaredBrowserPassed = [bool]($layerStatus -and $layerStatus.browser_smoke_passed -eq $true)

$dataRowsDone = ($canonicalRows -eq 100 -and $uniqueIds -eq 100 -and $declaredVisibleRows -eq 100)
$browserAcceptanceAlreadyDone = ($declaredBrowserPassed -and $declaredBrowserRows -ge 100)
$reconciliation = if ($dataRowsDone -and -not $browserAcceptanceAlreadyDone) {
    'DATA_ROWS_100_DONE_BROWSER_ACCEPTANCE_BLOCKED_AT_PREVIOUS_PROOF'
} elseif ($dataRowsDone -and $browserAcceptanceAlreadyDone) {
    'DATA_ROWS_100_AND_BROWSER_ACCEPTANCE_ALREADY_PROVEN'
} else {
    'DATA_ROWS_100_NOT_PROVEN'
}

if ($canonicalRows -ne 100) { $blockers.Add("CANONICAL_ROW_COUNT_MISMATCH:actual=$canonicalRows expected=100") }
if ($uniqueIds -ne 100) { $blockers.Add("UNIQUE_ROW_COUNT_MISMATCH:actual=$uniqueIds expected=100") }
if ($declaredVisibleRows -ne 100) { $blockers.Add("STATUS_VISIBLE_ROW_COUNT_MISMATCH:actual=$declaredVisibleRows expected=100") }

$httpUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json?slot=gas_emissions_1&expected=100&ts=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$httpRows = -1
$httpUniqueRows = -1
$httpError = $null
for ($attempt = 1; $attempt -le 5; $attempt++) {
    try {
        $served = Invoke-RestMethod -Uri $httpUrl -Method Get -TimeoutSec 20 -Headers @{ 'Cache-Control' = 'no-cache' }
        $httpRows = @($served.rows).Count
        $httpUniqueRows = @($served.rows | ForEach-Object { [string]$_.row_id } | Select-Object -Unique).Count
        if ($httpRows -eq 100 -and $httpUniqueRows -eq 100) { break }
    } catch {
        $httpError = $_.Exception.Message
    }
    Start-Sleep -Seconds 2
}
if ($httpRows -ne 100 -or $httpUniqueRows -ne 100) {
    $blockers.Add("HTTP_8012_100_ROWS_NOT_PROVEN:rows=$httpRows unique=$httpUniqueRows error=$httpError")
}

$browser = [ordered]@{
    status = 'NOT_RUN'
    url = $null
    expected_row_count = 100
    unique_row_count = 0
    latest_expected_count = $latestCount
    new_marker_count = 0
    manual_marker_on_new_count = 0
    expected_latest_rows_present = $false
    required_headers_present = $false
    headers = @()
    page_infos = @()
    console_errors = @()
    error = $null
}

if ($blockers.Count -eq 0) {
    $tmpBase = Join-Path ([System.IO.Path]::GetTempPath()) ('aays_gas_emissions_1_100_' + [Guid]::NewGuid().ToString('N'))
    $tmpExpected = $tmpBase + '.expected.json'
    $tmpScript = $tmpBase + '.py'
    $tmpResult = $tmpBase + '.result.json'
    Write-Json $tmpExpected ([object[]]@($latestIds))

    $pythonSource = @'
import json, math, re, sys, time
from pathlib import Path

out_path = Path(sys.argv[1])
expected_ids = set(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8-sig")))
target = 100
url = f"http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?slot=gas_emissions_1&expected=100&ts={int(time.time())}"
result = {
    "status": "FAIL",
    "url": url,
    "expected_row_count": target,
    "unique_row_count": 0,
    "latest_expected_count": len(expected_ids),
    "new_marker_count": 0,
    "manual_marker_on_new_count": 0,
    "expected_latest_rows_present": False,
    "required_headers_present": False,
    "headers": [],
    "page_infos": [],
    "console_errors": [],
    "error": None,
}
driver = None
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select, WebDriverWait

    options = webdriver.ChromeOptions()
    for arg in ("--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1920,1400"):
        options.add_argument(arg)
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    wait = WebDriverWait(driver, 90)
    wait.until(lambda d: d.find_element(By.ID, "layerSelect"))
    Select(driver.find_element(By.ID, "layerSelect")).select_by_value("gas")
    wait.until(lambda d: "100 satır" in d.find_element(By.ID, "pageInfo").text)

    rows = {}
    for _ in range(max(1, math.ceil(target / 25)) + 2):
        info = driver.find_element(By.ID, "pageInfo").text.strip()
        result["page_infos"].append(info)
        for tr in driver.find_elements(By.CSS_SELECTOR, "#table tbody tr"):
            cells = tr.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                row_id = cells[1].text.strip()
                if row_id:
                    rows[row_id] = cells[0].text.strip()
        match = re.search(r"Sayfa\s+(\d+)\s*/\s*(\d+)", info)
        if not match or int(match.group(1)) >= int(match.group(2)):
            break
        next_page = int(match.group(1)) + 1
        driver.find_element(By.ID, "next").click()
        wait.until(lambda d, p=next_page: re.search(rf"Sayfa\s+{p}\s*/", d.find_element(By.ID, "pageInfo").text))

    headers = [element.text.strip() for element in driver.find_elements(By.CSS_SELECTOR, "#table thead th")]
    required_headers = {
        "Hesap açıklaması", "Parcel binding", "Ham yerel kaynak", "Visible artifact",
        "Status yolu", "Rapor yolu", "Served commit", "Artifact SHA",
    }
    try:
        severe = [entry for entry in driver.get_log("browser") if str(entry.get("level", "")).upper() == "SEVERE"]
    except Exception:
        severe = []

    new_count = sum("YENİ / LATEST" in rows.get(row_id, "") for row_id in expected_ids)
    manual_count = sum("MANUEL İNCELEME" in rows.get(row_id, "") for row_id in expected_ids)
    expected_present = expected_ids.issubset(rows)
    headers_present = required_headers.issubset(set(headers))
    passed = (
        len(rows) == target
        and expected_present
        and new_count == len(expected_ids)
        and manual_count == len(expected_ids)
        and headers_present
        and not severe
    )
    result.update({
        "status": "PASS" if passed else "FAIL",
        "unique_row_count": len(rows),
        "new_marker_count": new_count,
        "manual_marker_on_new_count": manual_count,
        "expected_latest_rows_present": expected_present,
        "required_headers_present": headers_present,
        "headers": headers,
        "console_errors": severe,
        "title": driver.title,
    })
    if not passed:
        result["error"] = "DOM_COUNT_IDS_MARKERS_HEADERS_OR_CONSOLE_CHECK_FAILED"
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

    [System.IO.File]::WriteAllText($tmpScript, $pythonSource, [System.Text.UTF8Encoding]::new($false))
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        & $pythonCommand.Source $tmpScript $tmpResult $tmpExpected
    } else {
        $pyCommand = Get-Command py -ErrorAction SilentlyContinue
        if ($pyCommand) { & $pyCommand.Source -3 $tmpScript $tmpResult $tmpExpected }
        else { $global:LASTEXITCODE = 127 }
    }
    $browserExit = $LASTEXITCODE
    if (Test-Path -LiteralPath $tmpResult) {
        $browser = Read-Json $tmpResult
    } else {
        $browser.status = 'FAIL'
        $browser.error = 'BROWSER_RESULT_FILE_NOT_CREATED'
    }
    if ($browserExit -ne 0 -or [string]$browser.status -ne 'PASS') {
        $blockers.Add("BROWSER_ACCEPTANCE_FAILED:$($browser.error)")
    }
    Remove-Item -LiteralPath $tmpScript, $tmpExpected, $tmpResult -Force -ErrorAction SilentlyContinue
}

$browserAccepted = (
    $blockers.Count -eq 0 -and
    [string]$browser.status -eq 'PASS' -and
    [int]$browser.unique_row_count -eq 100 -and
    @($browser.console_errors).Count -eq 0
)

$head = $null
try { $head = (& git rev-parse HEAD 2>$null | Select-Object -First 1).Trim() } catch {}
$now = (Get-Date).ToUniversalTime().ToString('o')
$finalStatus = if ($browserAccepted) { 'PASS_100_OF_100_BROWSER_ACCEPTANCE' } else { 'BLOCKED_100_OF_100_BROWSER_ACCEPTANCE' }
$primaryBlocker = if ($blockers.Count -gt 0) { [string]$blockers[0] } else { $null }

$payload = [ordered]@{
    schema_version = 1
    task_id = $taskId
    slot_id = 'gas_emissions_1'
    base_slot_id = 'gas_emissions'
    shard_index = 1
    parcel_partition = [ordered]@{ start = 1; end = 30761; count = 30761; canonical_count = 92283 }
    status = $finalStatus
    generated_at = $now
    child_head = $head
    first_unverified_step = 'RECONCILE_DONE_VS_BLOCKED_THEN_100_OF_100_BROWSER_ACCEPTANCE'
    reconciliation = [ordered]@{
        conclusion = $reconciliation
        canonical_rows = $canonicalRows
        unique_row_ids = $uniqueIds
        status_visible_rows = $declaredVisibleRows
        status_browser_passed = $declaredBrowserPassed
        status_browser_rows = $declaredBrowserRows
        proof_37_status = if ($proof37) { [string]$proof37.status } else { $null }
        proof_66_status = if ($proof66) { [string]$proof66.status } else { $null }
        data_rows_100_done = $dataRowsDone
        browser_acceptance_100_previously_done = $browserAcceptanceAlreadyDone
    }
    http_acceptance = [ordered]@{
        url = $httpUrl
        served_rows = $httpRows
        served_unique_rows = $httpUniqueRows
        error = $httpError
        passed = ($httpRows -eq 100 -and $httpUniqueRows -eq 100)
    }
    browser_acceptance = $browser
    browser_acceptance_100_passed = $browserAccepted
    blockers = [string[]]@($blockers)
    primary_blocker = $primaryBlocker
    next_step = if ($browserAccepted) { 'KEEP_PARCEL_BINDING_GATE_FALSE_AND_CONTINUE_FIRST_UNVERIFIED_REAL_PARCEL_BINDING_EVIDENCE' } else { 'REPAIR_LIVE_8012_OR_DOM_BROWSER_PROOF_THEN_RERUN_SAME_100_ROW_ACCEPTANCE' }
    source = [ordered]@{
        name = 'GOV.UK DESNZ 2005 to 2023 local authority greenhouse gas emissions dataset'
        url = 'https://www.gov.uk/csv-preview/68653c7ee6c3cc924228943f/2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv'
        snapshot_date = '2025-08-19'
        measurement_level = 'local_authority'
        parcel_binding = 'not_proven'
    }
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

Write-Json $outputPath $payload
Write-Json $statusOutputPath ([ordered]@{
    task_id = $taskId
    slot_id = 'gas_emissions_1'
    state = $finalStatus
    blocker = $primaryBlocker
    report_path = $outputRel
    browser_acceptance_100_passed = $browserAccepted
    parcel_binding_gate_passed = $false
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    updated_at = $now
})

Write-Output ($payload | ConvertTo-Json -Depth 100)
exit 0
