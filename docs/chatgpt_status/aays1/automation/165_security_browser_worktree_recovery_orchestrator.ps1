$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }

$taskId = 'aays1-137-next-batch-source-fetch-20260710'
$recoveryId = 'aays1-165-security-browser-worktree-recovery-20260713'
$startedAt = (Get-Date).ToUniversalTime().ToString('o')

$script103Rel = 'docs/chatgpt_status/aays1/automation/103_security_accuracy_count_expansion.ps1'
$script145Rel = 'docs/chatgpt_status/aays1/automation/145_security_official_api_lsoa_validation.ps1'
$script147Rel = 'docs/chatgpt_status/aays1/automation/147_security_300_browser_validation.ps1'
$script146Rel = 'docs/chatgpt_status/aays1/automation/146_security_strict_multiwork_orchestrator.ps1'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/165_security_browser_worktree_recovery_orchestrator.json'

$script103Path = Join-Path $repoRoot ($script103Rel -replace '/', '\')
$script145Path = Join-Path $repoRoot ($script145Rel -replace '/', '\')
$script147Path = Join-Path $repoRoot ($script147Rel -replace '/', '\')
$script146Path = Join-Path $repoRoot ($script146Rel -replace '/', '\')
$outputPath = Join-Path $repoRoot ($outputRel -replace '/', '\')
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outputPath) | Out-Null

$result = [ordered]@{
  task_id = $taskId
  recovery_id = $recoveryId
  status = 'started'
  started_at = $startedAt
  completed_at = $null
  repo_root = $repoRoot
  canonical_storage = 'F_PORTABLE_ROOT'
  single_runner_only = $true
  parallel_runner = $false
  patched_scripts = @()
  parser_error_count_103 = $null
  parser_error_count_145 = $null
  parser_error_count_147 = $null
  child_orchestrator = $script146Rel
  child_exit_code = $null
  child_output_tail = $null
  child_status = $null
  selected_verified_rows = $null
  added_rows = $null
  score_4_count = $null
  manual_review_count = $null
  official_latest_month = $null
  unique_lsoa_count = $null
  lsoa_http_200_count = $null
  browser_status = $null
  browser_engine = $null
  browser_url = $null
  latest_filter_rows = $null
  console_error_count = $null
  site_data_published = $false
  git_push_status = $null
  remote_readback_status = $null
  blockers = @()
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  person_level_data = $false
}

function Save-Result {
  $result | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $outputPath -Encoding UTF8
}

function Parse-ErrorCount([string]$path) {
  $tokens = $null
  $errors = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
  return @($errors).Count
}

function Read-Json([string]$rel) {
  $path = Join-Path $repoRoot ($rel -replace '/', '\')
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  try { return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}

try {
  foreach ($path in @($script103Path,$script145Path,$script147Path,$script146Path)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "missing_script:$path" }
  }

  $source103 = Get-Content -LiteralPath $script103Path -Raw -Encoding UTF8
  $replacements103 = [ordered]@{
    'throw "baseline_count_not_$baselineExpected:$($baselineRows.Count)"' = 'throw "baseline_count_not_${baselineExpected}:$($baselineRows.Count)"'
    'features = @($verifiedFeatures)' = 'features = $verifiedFeatures.ToArray()'
    'rows = @($visibleRows)' = 'rows = $visibleRows.ToArray()'
    '$newRows = @($visibleRows | Where-Object { $_.is_new_in_latest_batch -eq $true })' = '$newRows = @($visibleRows.ToArray() | Where-Object { $_.is_new_in_latest_batch -eq $true })'
  }
  $changed103 = $false
  foreach ($pair in $replacements103.GetEnumerator()) {
    if ($source103.Contains($pair.Key)) { $source103 = $source103.Replace($pair.Key,$pair.Value); $changed103 = $true }
  }
  if ($changed103) {
    [System.IO.File]::WriteAllText($script103Path,$source103,[System.Text.UTF8Encoding]::new($false))
    $result.patched_scripts += $script103Rel
  }

  $source145 = Get-Content -LiteralPath $script145Path -Raw -Encoding UTF8
  $changed145 = $false
  $bad145 = '"lsoa_api_validation_failed:$lsoa:$($_.Exception.Message)"'
  $good145 = '"lsoa_api_validation_failed:${lsoa}:$($_.Exception.Message)"'
  if ($source145.Contains($bad145)) { $source145 = $source145.Replace($bad145,$good145); $changed145 = $true }
  if ($changed145) {
    [System.IO.File]::WriteAllText($script145Path,$source145,[System.Text.UTF8Encoding]::new($false))
    $result.patched_scripts += $script145Rel
  }

  $fixed147 = @'
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
  browser_engine = $null
  browser_url = $null
  visible_rows_text = $null
  geojson_metric_present = $false
  latest_filter_rows = $null
  source_link_count = 0
  artifact_link_count = 0
  console_error_count = $null
  worktree_http_server_started = $false
  worktree_http_server_url = 'http://127.0.0.1:8020/'
  diagnostics = @()
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
import json, os, shutil, sys, tempfile, time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

out = Path(sys.argv[1])
urls = sys.argv[2:]
proof = {
    "status":"failed", "browser_engine":None, "url":None,
    "visible_rows_text":None, "geojson_metric_present":False,
    "latest_filter_rows":None, "source_link_count":0,
    "artifact_link_count":0, "console_error_count":None,
    "console_errors":[], "diagnostics":[], "error":None
}

common_args = [
    "--headless=new", "--disable-gpu", "--no-sandbox",
    "--disable-dev-shm-usage", "--disable-extensions",
    "--no-first-run", "--no-default-browser-check",
    "--remote-allow-origins=*", "--window-size=1920,1080"
]

def first_existing(paths):
    for p in paths:
        if p and Path(p).exists():
            return p
    return None

def chrome_factory():
    opts = ChromeOptions()
    for arg in common_args: opts.add_argument(arg)
    profile = tempfile.mkdtemp(prefix="aays_chrome_")
    opts.add_argument("--user-data-dir=" + profile)
    opts.set_capability("goog:loggingPrefs", {"browser":"ALL"})
    binary = first_existing([
        shutil.which("chrome"), shutil.which("google-chrome"), shutil.which("chrome.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ])
    if binary: opts.binary_location = binary
    driver_bin = shutil.which("chromedriver") or shutil.which("chromedriver.exe")
    service = ChromeService(executable_path=driver_bin) if driver_bin else ChromeService()
    return webdriver.Chrome(service=service, options=opts), profile, "chrome"

def edge_factory():
    opts = EdgeOptions()
    for arg in common_args: opts.add_argument(arg)
    profile = tempfile.mkdtemp(prefix="aays_edge_")
    opts.add_argument("--user-data-dir=" + profile)
    opts.set_capability("goog:loggingPrefs", {"browser":"ALL"})
    binary = first_existing([
        shutil.which("msedge"), shutil.which("msedge.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe")
    ])
    if binary: opts.binary_location = binary
    driver_bin = shutil.which("msedgedriver") or shutil.which("msedgedriver.exe")
    service = EdgeService(executable_path=driver_bin) if driver_bin else EdgeService()
    return webdriver.Edge(service=service, options=opts), profile, "edge"

for factory in (chrome_factory, edge_factory):
    for url in urls:
        driver = None
        profile = None
        engine = None
        try:
            driver, profile, engine = factory()
            driver.set_page_load_timeout(60)
            driver.get(url)
            WebDriverWait(driver, 45).until(EC.presence_of_element_located((By.ID,"table")))
            WebDriverWait(driver, 45).until(lambda d: "Security / Public Safety" in d.find_element(By.ID,"title").text)
            WebDriverWait(driver, 45).until(lambda d: "300 satır" in d.find_element(By.ID,"pageInfo").text)
            time.sleep(2)
            body = driver.find_element(By.TAG_NAME,"body").text
            visible_text = next((line for line in body.splitlines() if "Görünür" in line and "satır" in line), None)
            geo_ok = "GeoJSON feature: 300" in body
            source_links = len(driver.find_elements(By.CSS_SELECTOR,'a[href^="https://data.police.uk"]'))
            artifact_links = len(driver.find_elements(By.CSS_SELECTOR,'a[data-artifact-link="true"]'))
            Select(driver.find_element(By.ID,"statusFilter")).select_by_value("latest")
            driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles:true}))", driver.find_element(By.ID,"statusFilter"))
            WebDriverWait(driver, 25).until(lambda d: "150 satır" in d.find_element(By.ID,"pageInfo").text)
            latest_text = driver.find_element(By.ID,"pageInfo").text
            logs = driver.get_log("browser")
            errors = [x for x in logs if x.get("level") == "SEVERE"]
            passed = (
                visible_text is not None and "300" in visible_text and geo_ok and
                "150 satır" in latest_text and source_links > 0 and artifact_links > 0 and
                len(errors) == 0
            )
            proof.update({
                "status":"pass" if passed else "failed", "browser_engine":engine,
                "url":url, "visible_rows_text":visible_text,
                "geojson_metric_present":geo_ok, "latest_filter_rows":latest_text,
                "source_link_count":source_links, "artifact_link_count":artifact_links,
                "console_error_count":len(errors), "console_errors":errors[:20]
            })
            if passed: break
            proof["diagnostics"].append(f"{engine} {url}: contract mismatch")
        except Exception as exc:
            label = engine or factory.__name__
            proof["diagnostics"].append(f"{label} {url}: {type(exc).__name__}: {exc}")
        finally:
            if driver is not None:
                try: driver.quit()
                except Exception: pass
            if profile:
                shutil.rmtree(profile, ignore_errors=True)
    if proof["status"] == "pass": break

if proof["status"] != "pass":
    proof["error"] = proof["diagnostics"][-1] if proof["diagnostics"] else "no_browser_attempt_passed"
out.write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8")
sys.exit(0 if proof["status"] == "pass" else 2)
'@

$server = $null
try {
  $tempPy = Join-Path $env:TEMP "aays1_security_300_browser_$PID.py"
  $pythonScript | Set-Content -Encoding UTF8 $tempPy

  try {
    $server = Start-Process -FilePath python -ArgumentList @('-m','http.server','8020','--bind','127.0.0.1','--directory',$repoRoot) -WindowStyle Hidden -PassThru
    for ($i=0; $i -lt 20; $i++) {
      Start-Sleep -Milliseconds 500
      try {
        $probe = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8020/' -TimeoutSec 2
        if ([int]$probe.StatusCode -eq 200) { $result.worktree_http_server_started = $true; break }
      } catch {}
    }
  } catch {
    $result.diagnostics += "worktree_http_server_start_failed:$($_.Exception.Message)"
  }

  $urls = @(
    'http://127.0.0.1:8020/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=147',
    'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=147'
  )
  & python $tempPy $proofPath @urls
  $browserExit = $LASTEXITCODE
  Remove-Item -Force -ErrorAction SilentlyContinue $tempPy
  if (-not (Test-Path $proofPath)) { throw 'browser_proof_not_written' }
  $proof = Get-Content -Raw -Encoding UTF8 $proofPath | ConvertFrom-Json
  $result.browser_status = [string]$proof.status
  $result.browser_engine = [string]$proof.browser_engine
  $result.browser_url = [string]$proof.url
  $result.visible_rows_text = [string]$proof.visible_rows_text
  $result.geojson_metric_present = [bool]$proof.geojson_metric_present
  $result.latest_filter_rows = [string]$proof.latest_filter_rows
  $result.source_link_count = [int]$proof.source_link_count
  $result.artifact_link_count = [int]$proof.artifact_link_count
  $result.console_error_count = $proof.console_error_count
  $result.diagnostics += @($proof.diagnostics)
  if ($browserExit -ne 0 -or $proof.status -ne 'pass') { $result.blockers += "browser_validation_failed:$($proof.error)" }
  if ($null -ne $result.console_error_count -and $result.console_error_count -ne 0) { $result.blockers += "browser_console_errors:$($result.console_error_count)" }
  $result.status = if ($result.blockers.Count -eq 0) { 'completed_300_rows_browser_pass' } else { 'blocked_300_rows_browser_validation' }
} catch {
  $result.status = 'blocked_300_rows_browser_exception'
  $result.blockers += $_.Exception.Message
} finally {
  if ($null -ne $server) { try { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue } catch {} }
}

$result | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $outPath
Write-Host "OUTPUT=$outPath"
if ($result.blockers.Count -gt 0 -or $result.browser_status -ne 'pass') { exit 2 }
exit 0
'@
  [System.IO.File]::WriteAllText($script147Path,$fixed147,[System.Text.UTF8Encoding]::new($false))
  $result.patched_scripts += $script147Rel

  $result.parser_error_count_103 = Parse-ErrorCount $script103Path
  $result.parser_error_count_145 = Parse-ErrorCount $script145Path
  $result.parser_error_count_147 = Parse-ErrorCount $script147Path
  if ($result.parser_error_count_103 -ne 0) { throw "103_parser_errors:$($result.parser_error_count_103)" }
  if ($result.parser_error_count_145 -ne 0) { throw "145_parser_errors:$($result.parser_error_count_145)" }
  if ($result.parser_error_count_147 -ne 0) { throw "147_parser_errors:$($result.parser_error_count_147)" }

  Save-Result
  $childOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $script146Path 2>&1
  $result.child_exit_code = $LASTEXITCODE
  $childText = ($childOutput | Out-String).Trim()
  if ($childText.Length -gt 16000) { $childText = $childText.Substring($childText.Length - 16000) }
  $result.child_output_tail = $childText

  $out103 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json'
  $out145 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/145_security_official_api_lsoa_validation.json'
  $out147 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/147_security_300_browser_validation.json'
  $out146 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/146_security_strict_multiwork_orchestrator.json'

  if ($null -ne $out103) {
    $result.selected_verified_rows = $out103.selected_count
    $result.added_rows = $out103.added_count
    $result.score_4_count = $out103.score_4_count
    $result.manual_review_count = $out103.manual_review_count
  }
  if ($null -ne $out145) {
    $result.official_latest_month = $out145.official_latest_month
    $result.unique_lsoa_count = $out145.unique_lsoa_count
    $result.lsoa_http_200_count = $out145.lsoa_http_200_count
  }
  if ($null -ne $out147) {
    $result.browser_status = $out147.browser_status
    $result.browser_engine = $out147.browser_engine
    $result.browser_url = $out147.browser_url
    $result.latest_filter_rows = $out147.latest_filter_rows
    $result.console_error_count = $out147.console_error_count
  }
  if ($null -ne $out146) {
    $result.child_status = $out146.status
    $result.site_data_published = [bool]$out146.site_data_published
    $result.git_push_status = $out146.git_push_status
    $result.remote_readback_status = $out146.remote_readback_status
    if ($out146.blockers) { $result.blockers += @($out146.blockers | ForEach-Object { "146:$_" }) }
  }

  if ($result.child_exit_code -eq 0 -and $result.child_status -eq 'completed_atomic_publish_remote_readback_pass') {
    $result.status = 'browser_recovery_strict_chain_completed'
  } else {
    $result.status = 'browser_recovery_strict_chain_blocked'
    if ($result.child_exit_code -ne 0) { $result.blockers += "child_orchestrator_exit_$($result.child_exit_code)" }
  }
} catch {
  $result.status = 'blocked_browser_worktree_recovery'
  $result.blockers += $_.Exception.Message
} finally {
  $result.completed_at = (Get-Date).ToUniversalTime().ToString('o')
  $result.blockers = @($result.blockers | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | Select-Object -Unique)
  Save-Result
}

Write-Host "OUTPUT=$outputPath"
if ($result.blockers.Count -gt 0 -or $result.child_exit_code -notin @(0,$null)) { exit 2 }
exit 0
