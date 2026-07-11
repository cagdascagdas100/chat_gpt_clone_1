$ErrorActionPreference = 'Continue'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$outRel = 'docs/chatgpt_status/aays1/runner_outputs/147_security_300_browser_validation.json'
$proofRel = 'docs/chatgpt_status/_shared/reports/security_300_rows_browser_validation_20260711.json'
$outPath = Join-Path $repoRoot $outRel
$proofPath = Join-Path $repoRoot $proofRel
New-Item -ItemType Directory -Force -Path (Split-Path $outPath),(Split-Path $proofPath) | Out-Null

$result = [ordered]@{
  task_id = 'aays1-147-security-300-browser-validation-20260711'
  page_key = 'aays1'
  status = 'started'
  checked_at = (Get-Date).ToString('o')
  expected_visible_rows = 300
  expected_new_batch_rows = 150
  expected_geojson_features = 300
  browser_status = 'not_run'
  browser_url = $null
  visible_rows_text = $null
  geojson_metric_present = $false
  latest_filter_rows = $null
  source_link_count = 0
  artifact_link_count = 0
  console_error_count = $null
  blockers = @()
  single_runner_only = $true
  parallel_runner = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}

$pythonScript = @'
import json, sys, time
from pathlib import Path
out = Path(sys.argv[1])
urls = sys.argv[2:]
proof = {
    "status":"failed", "url":None, "visible_rows_text":None,
    "geojson_metric_present":False, "latest_filter_rows":None,
    "source_link_count":0, "artifact_link_count":0,
    "console_error_count":None, "console_errors":[], "error":None
}
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1920,1080")
    opts.set_capability("goog:loggingPrefs", {"browser":"ALL"})
    last = None
    for url in urls:
        driver = None
        try:
            driver = webdriver.Chrome(options=opts)
            driver.get(url)
            WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.ID,"table")))
            WebDriverWait(driver, 40).until(lambda d: "Security / Public Safety" in d.find_element(By.ID,"title").text)
            WebDriverWait(driver, 40).until(lambda d: "300 satır" in d.find_element(By.ID,"pageInfo").text)
            time.sleep(2)
            body = driver.find_element(By.TAG_NAME,"body").text
            visible_text = next((line for line in body.splitlines() if "Görünür satır" in line), None)
            geo_ok = "GeoJSON feature: 300" in body
            source_links = len(driver.find_elements(By.CSS_SELECTOR,'a[href^="https://data.police.uk"]'))
            artifact_links = len(driver.find_elements(By.CSS_SELECTOR,'a[data-artifact-link="true"]'))
            Select(driver.find_element(By.ID,"statusFilter")).select_by_value("latest")
            driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles:true}))", driver.find_element(By.ID,"statusFilter"))
            WebDriverWait(driver, 20).until(lambda d: "150 satır" in d.find_element(By.ID,"pageInfo").text)
            latest_text = driver.find_element(By.ID,"pageInfo").text
            logs = driver.get_log("browser")
            errors = [x for x in logs if x.get("level") == "SEVERE"]
            passed = (
                visible_text is not None and "300" in visible_text and geo_ok and
                "150 satır" in latest_text and source_links > 0 and artifact_links > 0 and
                len(errors) == 0
            )
            proof.update({
                "status":"pass" if passed else "failed", "url":url,
                "visible_rows_text":visible_text, "geojson_metric_present":geo_ok,
                "latest_filter_rows":latest_text, "source_link_count":source_links,
                "artifact_link_count":artifact_links, "console_error_count":len(errors),
                "console_errors":errors[:20]
            })
            if passed:
                break
        except Exception as exc:
            last = repr(exc)
        finally:
            if driver is not None:
                driver.quit()
    if proof["status"] != "pass":
        proof["error"] = proof.get("error") or last or "no_browser_url_passed"
except Exception as exc:
    proof["error"] = repr(exc)
out.write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8")
sys.exit(0 if proof["status"] == "pass" else 2)
'@

try {
  $tempPy = Join-Path $env:TEMP "aays1_security_300_browser_$PID.py"
  $pythonScript | Set-Content -Encoding UTF8 $tempPy
  $urls = @(
    'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=147',
    'http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=147',
    'http://127.0.0.1:8020/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=147'
  )
  & python $tempPy $proofPath @urls
  $browserExit = $LASTEXITCODE
  Remove-Item -Force -ErrorAction SilentlyContinue $tempPy
  if (-not (Test-Path $proofPath)) { throw 'browser_proof_not_written' }
  $proof = Get-Content -Raw -Encoding UTF8 $proofPath | ConvertFrom-Json
  $result.browser_status = [string]$proof.status
  $result.browser_url = [string]$proof.url
  $result.visible_rows_text = [string]$proof.visible_rows_text
  $result.geojson_metric_present = [bool]$proof.geojson_metric_present
  $result.latest_filter_rows = [string]$proof.latest_filter_rows
  $result.source_link_count = [int]$proof.source_link_count
  $result.artifact_link_count = [int]$proof.artifact_link_count
  $result.console_error_count = $proof.console_error_count
  if ($browserExit -ne 0 -or $proof.status -ne 'pass') { $result.blockers += "browser_validation_failed:$($proof.error)" }
  if ($result.console_error_count -ne 0) { $result.blockers += "browser_console_errors:$($result.console_error_count)" }
  $result.status = if ($result.blockers.Count -eq 0) { 'completed_300_rows_browser_pass' } else { 'blocked_300_rows_browser_validation' }
} catch {
  $result.status = 'blocked_300_rows_browser_exception'
  $result.blockers += $_.Exception.Message
}

$result | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $outPath
Write-Host "OUTPUT=$outPath"
if ($result.blockers.Count -gt 0 -or $result.browser_status -ne 'pass') { exit 2 }
exit 0
