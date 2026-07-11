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
    (($Value | ConvertTo-Json -Depth 60) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
}

function Get-RowCountFromJson([string]$Path) {
  $obj = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($null -eq $obj.rows) { return -1 }
  return @($obj.rows).Count
}

function Copy-Atomic([string]$Source, [string]$Target) {
  Ensure-Dir (Split-Path -Parent $Target)
  $tmp = $Target + '.aays_tmp_' + [Guid]::NewGuid().ToString('N')
  Copy-Item -LiteralPath $Source -Destination $tmp -Force
  Move-Item -LiteralPath $tmp -Destination $Target -Force
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$taskId = [string]$env:AAYS_TASK_ID
$pageKey = [string]$env:AAYS_PAGE_KEY
$branch = [string]$env:AAYS_TARGET_BRANCH

if (-not $repoRoot -or -not $taskId -or $pageKey -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_V2_MUST_RUN_INSIDE_CANONICAL_SHARED_RUNNER'
}
if ($branch -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_V2_WRONG_BRANCH'
}

$portableRoot = 'F:\TerraYield_AAYS_Portable'
$servedRepoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$matrixRel = 'england_map_web\TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$rowsRel = 'england_map_web\data\program_layer_matrix\gas_emissions_visible_rows_latest.json'
$statusRel = 'england_map_web\data\program_layer_matrix\gas_emissions_status_latest.json'
$blockerRel = 'docs\chatgpt_status\gas_emissions\status\149_gas_emissions_8012_visibility_blocker_20260711_latest.json'

$sourceRows = Join-Path $repoRoot $rowsRel
$sourceStatus = Join-Path $repoRoot $statusRel
$sourceMatrix = Join-Path $repoRoot $matrixRel
$sourceBlocker = Join-Path $repoRoot $blockerRel

foreach ($required in @($sourceRows,$sourceStatus,$sourceMatrix)) {
  if (-not (Test-Path -LiteralPath $required)) { throw "MISSING_CANONICAL_FILE: $required" }
}

$canonicalCount = Get-RowCountFromJson $sourceRows
if ($canonicalCount -ne 28) { throw "CANONICAL_ROW_COUNT_NOT_28: $canonicalCount" }

if (-not (Test-Path -LiteralPath $servedRepoRoot)) {
  throw 'CANONICAL_SERVED_REPO_ROOT_NOT_FOUND'
}
if (-not ([System.IO.Path]::GetFullPath($servedRepoRoot).StartsWith([System.IO.Path]::GetFullPath($portableRoot), [System.StringComparison]::OrdinalIgnoreCase))) {
  throw 'SERVED_ROOT_OUTSIDE_PORTABLE_ROOT'
}

$gitPullStatus = 'not_attempted'
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
  try {
    $dirty = @(& $git.Source -C $servedRepoRoot status --porcelain 2>$null)
    if (@($dirty).Count -eq 0) {
      & $git.Source -C $servedRepoRoot fetch origin $branch | Out-Null
      & $git.Source -C $servedRepoRoot checkout $branch | Out-Null
      & $git.Source -C $servedRepoRoot pull --ff-only origin $branch | Out-Null
      if ($LASTEXITCODE -eq 0) { $gitPullStatus = 'ff_only_pulled' } else { $gitPullStatus = 'ff_only_pull_failed_copy_fallback' }
    } else {
      $gitPullStatus = 'served_repo_dirty_copy_fallback'
    }
  } catch {
    $gitPullStatus = 'git_exception_copy_fallback'
  }
}

$publishFiles = @(
  @{ Source=$sourceRows; Target=(Join-Path $servedRepoRoot $rowsRel) },
  @{ Source=$sourceStatus; Target=(Join-Path $servedRepoRoot $statusRel) },
  @{ Source=$sourceMatrix; Target=(Join-Path $servedRepoRoot $matrixRel) }
)
foreach ($item in $publishFiles) {
  $sourceHash = (Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash
  $targetHash = if (Test-Path -LiteralPath $item.Target) { (Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash } else { '' }
  if ($sourceHash -ne $targetHash) { Copy-Atomic $item.Source $item.Target }
}

$servedRowsLocal = Join-Path $servedRepoRoot $rowsRel
$servedCountLocal = Get-RowCountFromJson $servedRowsLocal
if ($servedCountLocal -ne 28) { throw "SERVED_LOCAL_ROW_COUNT_NOT_28: $servedCountLocal" }

$servedHead = 'not_available'
if ($git) {
  try { $servedHead = ((& $git.Source -C $servedRepoRoot rev-parse HEAD) | Select-Object -First 1).Trim() } catch {}
}
$artifactSha256 = (Get-FileHash -LiteralPath $servedRowsLocal -Algorithm SHA256).Hash.ToLowerInvariant()

$httpRowsUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json?publish_v2=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$httpCount = -1
$httpError = $null
for ($i=0; $i -lt 12; $i++) {
  try {
    $resp = Invoke-RestMethod -Uri $httpRowsUrl -Method Get -TimeoutSec 15 -Headers @{ 'Cache-Control'='no-cache' }
    $httpCount = @($resp.rows).Count
    if ($httpCount -eq 28) { break }
  } catch { $httpError = $_.Exception.Message }
  Start-Sleep -Seconds 2
}
if ($httpCount -ne 28) { throw "HTTP_8012_ROW_COUNT_NOT_28: $httpCount $httpError" }

$reportRel = 'docs/chatgpt_status/gas_emissions/reports/150_gas_emissions_8012_publish_and_browser_smoke_28_20260711.json'
$resultStatusRel = 'docs/chatgpt_status/gas_emissions/status/150_gas_emissions_8012_publish_and_browser_smoke_28_latest.json'
$reportPath = Join-Path $repoRoot ($reportRel -replace '/', '\')
$resultStatusPath = Join-Path $repoRoot ($resultStatusRel -replace '/', '\')
$canonicalStatusPath = Join-Path $repoRoot $statusRel
$blockerPath = Join-Path $repoRoot $blockerRel

$tmpBase = Join-Path ([System.IO.Path]::GetTempPath()) $taskId
$tmpPy = $tmpBase + '.py'
$tmpOut = $tmpBase + '.json'

$pythonSource = @'
import json
import sys
import time
from pathlib import Path

out_path = Path(sys.argv[1])
url = "http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=gas28v2&ts=" + str(int(time.time()))
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
    "unique_row_count": 0,
    "new_marker_count": 0,
    "manual_marker_on_new_count": 0,
    "expected_new_rows_present": False,
    "page_info": "",
    "console_errors": [],
    "error": None,
}
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
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    wait = WebDriverWait(driver, 45)
    wait.until(lambda d: d.find_element(By.ID, "layerSelect"))
    Select(driver.find_element(By.ID, "layerSelect")).select_by_value("gas")
    wait.until(lambda d: "28 satır" in d.find_element(By.ID, "pageInfo").text)

    row_map = {}
    def collect_rows():
        for row in driver.find_elements(By.CSS_SELECTOR, "#table tbody tr"):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 2:
                continue
            row_id = cells[1].text.strip()
            if row_id:
                row_map[row_id] = cells[0].text.strip()

    collect_rows()
    next_button = driver.find_element(By.ID, "next")
    next_button.click()
    wait.until(lambda d: "Sayfa 2 / 2" in d.find_element(By.ID, "pageInfo").text)
    collect_rows()

    page_info = driver.find_element(By.ID, "pageInfo").text.strip()
    severe = []
    try:
        severe = [e for e in driver.get_log("browser") if str(e.get("level", "")).upper() == "SEVERE"]
    except Exception:
        severe = []

    present = expected_ids.issubset(set(row_map))
    new_marker_count = sum(1 for rid in expected_ids if "YENİ / LATEST" in row_map.get(rid, ""))
    manual_marker_count = sum(1 for rid in expected_ids if "MANUEL İNCELEME" in row_map.get(rid, ""))
    passed = len(row_map) == 28 and present and new_marker_count == 4 and manual_marker_count == 4 and not severe
    result.update({
        "status": "PASS" if passed else "FAIL",
        "rendered_row_count": 28 if len(row_map) == 28 else len(row_map),
        "unique_row_count": len(row_map),
        "rendered_row_ids": sorted(row_map),
        "expected_new_rows_present": present,
        "expected_new_row_ids": sorted(expected_ids),
        "new_marker_count": new_marker_count,
        "manual_marker_on_new_count": manual_marker_count,
        "page_info": page_info,
        "console_errors": severe,
        "title": driver.title,
    })
    if not passed:
        result["error"] = "row_count_new_markers_manual_markers_or_console_check_failed"
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

if (-not (Test-Path -LiteralPath $tmpOut)) { throw 'SELENIUM_RESULT_NOT_WRITTEN' }
$result = Get-Content -LiteralPath $tmpOut -Raw -Encoding UTF8 | ConvertFrom-Json
$passed = ($exitCode -eq 0 -and [string]$result.status -eq 'PASS' -and [int]$result.unique_row_count -eq 28 -and [int]$result.new_marker_count -eq 4)

$payload = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  target_branch = $branch
  status = if ($passed) { 'PASS' } else { 'FAIL' }
  generated_by_runner = $true
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  publish_root = $servedRepoRoot
  publish_git_status = $gitPullStatus
  served_commit_sha = $servedHead
  artifact_sha256 = $artifactSha256
  canonical_row_count = $canonicalCount
  served_local_row_count = $servedCountLocal
  served_http_row_count = $httpCount
  browser = $result.browser
  url = $result.url
  rendered_row_count = [int]$result.rendered_row_count
  unique_row_count = [int]$result.unique_row_count
  expected_new_rows_present = [bool]$result.expected_new_rows_present
  expected_new_row_ids = @($result.expected_new_row_ids)
  new_marker_count = [int]$result.new_marker_count
  manual_marker_on_new_count = [int]$result.manual_marker_on_new_count
  page_info = [string]$result.page_info
  console_errors = @($result.console_errors)
  error = $result.error
  source_rows_path = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
  canonical_status_path = 'england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
  report_path = $reportRel
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
  git_push_status = 'pending_runner_wrapper'
}
Write-Json $reportPath $payload
Write-Json $resultStatusPath $payload

if ($passed) {
  $canonical = Get-Content -LiteralPath $canonicalStatusPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $canonical.browser_smoke_passed = $true
  $canonical | Add-Member -NotePropertyName browser_smoke_row_count -NotePropertyValue 28 -Force
  $canonical | Add-Member -NotePropertyName browser_smoke_new_marker_count -NotePropertyValue 4 -Force
  $canonical | Add-Member -NotePropertyName browser_smoke_report_path -NotePropertyValue $reportRel -Force
  $canonical | Add-Member -NotePropertyName browser_smoke_passed_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
  $canonical | Add-Member -NotePropertyName served_publish_root -NotePropertyValue $servedRepoRoot -Force
  $canonical | Add-Member -NotePropertyName served_commit_sha -NotePropertyValue $servedHead -Force
  $canonical | Add-Member -NotePropertyName artifact_sha256 -NotePropertyValue $artifactSha256 -Force
  $canonical.next_required_runner_action = 'Continue official GOV.UK source expansion in a small batch, then begin parcel-level matching without inventing allocation or geometry.'
  $canonical.final_ready = $false
  $canonical.product_final_ready = $false
  $canonical.fake_data = $false
  Write-Json $canonicalStatusPath $canonical

  if (Test-Path -LiteralPath $blockerPath) {
    $blocker = Get-Content -LiteralPath $blockerPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $blocker.status = 'RESOLVED_8012_VISIBLE_28_BROWSER_PASS'
    $blocker.local_8012_visible_rows = 28
    $blocker.browser_smoke_28_passed = $true
    $blocker.new_data_expansion_paused = $false
    $blocker | Add-Member -NotePropertyName resolved_report_path -NotePropertyValue $reportRel -Force
    $blocker | Add-Member -NotePropertyName resolved_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
    $blocker.final_ready = $false
    $blocker.product_final_ready = $false
    $blocker.fake_data = $false
    Write-Json $blockerPath $blocker
  }
}

Remove-Item -LiteralPath $tmpPy,$tmpOut -Force -ErrorAction SilentlyContinue
if (-not $passed) { throw 'GAS_EMISSIONS_28_PUBLISH_AND_BROWSER_SMOKE_V2_FAILED' }
Write-Output ($payload | ConvertTo-Json -Depth 60)
