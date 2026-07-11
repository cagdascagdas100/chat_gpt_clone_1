[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }
function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}
function Write-Json([string]$Path, [object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText(
    $Path,
    (($Value | ConvertTo-Json -Depth 40) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or -not $repoRoot.StartsWith('F:\TerraYield_AAYS_Portable\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw 'TOPOGRAPHY_155_REQUIRES_F_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'topography-155-site-latest-results-visibility-fix-20260711' }
$branch = if ($env:AAYS_TARGET_BRANCH) { [string]$env:AAYS_TARGET_BRANCH } else { 'codex/aays-single-runner-v5-20260706' }
$startedAt = Now-Utc

$htmlRel = 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$rowsRel = 'england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$statusWebRel = 'england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$browserProofRel = 'docs/chatgpt_status/topography/reports/155_topography_site_latest_results_browser_validation_20260711.json'
$statusRel = 'docs/chatgpt_status/topography/status/155_topography_site_latest_results_visibility_fix_latest.json'
$runnerOutputRel = 'docs/chatgpt_status/topography/runner_outputs/155_topography_site_latest_results_visibility_fix.json'

$htmlPath = Join-Path $repoRoot ($htmlRel -replace '/', '\')
$rowsPath = Join-Path $repoRoot ($rowsRel -replace '/', '\')
$statusWebPath = Join-Path $repoRoot ($statusWebRel -replace '/', '\')

foreach ($required in @($htmlPath, $rowsPath, $statusWebPath)) {
  if (-not (Test-Path -LiteralPath $required)) { throw "REQUIRED_FILE_MISSING:$required" }
}

$htmlText = Get-Content -LiteralPath $htmlPath -Raw -Encoding UTF8
$rowsData = Get-Content -LiteralPath $rowsPath -Raw -Encoding UTF8 | ConvertFrom-Json
$statusData = Get-Content -LiteralPath $statusWebPath -Raw -Encoding UTF8 | ConvertFrom-Json
$rows = @($rowsData.rows)

$staticChecks = [ordered]@{
  html_uses_visible_rows = $htmlText.Contains('data/program_layer_matrix/topography_visible_rows_latest.json')
  html_uses_visible_status = $htmlText.Contains('data/program_layer_matrix/topography_visible_status_latest.json')
  html_has_latest_filter = $htmlText.Contains('Yalnız yeni / latest')
  row_count = $rows.Count
  required_badge_rows = @($rows | Where-Object { $_.display_badge -eq 'COPERNICUS_ODATA_QUERY_CONTRACT_READY' }).Count
  required_grid_rows = @($rows | Where-Object { $_.copdem_grid_id -eq 'N51_W001' }).Count
  required_queue_rows = @($rows | Where-Object { [string]$_.queue_path -eq 'docs/chatgpt_status/topography/queue/154_topography_copdem_odata_geocell_sampling_20260711.task.json' }).Count
  numeric_elevation_rows = @($rows | Where-Object { $null -ne $_.elevation_sea_level_m }).Count
}

$python = $null
foreach ($candidate in @('python','py')) {
  $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
  if ($cmd) { $python = $cmd.Source; break }
}
if (-not $python) { throw 'PYTHON_NOT_FOUND_FOR_SELENIUM_VALIDATION' }

$tempPy = Join-Path $env:TEMP ("aays_topography_155_" + [guid]::NewGuid().ToString('N') + '.py')
$tempJson = Join-Path $env:TEMP ("aays_topography_155_" + [guid]::NewGuid().ToString('N') + '.json')
$pyCode = @'
import json, sys, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

out_path = sys.argv[1]
url = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?topography_browser_validation=155'
options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920,1080')
options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
driver = webdriver.Chrome(options=options)
result = {'status': 'FAIL', 'browser': 'Google Chrome via Selenium', 'url': url}
try:
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'layerSelect')))
    Select(driver.find_element(By.ID, 'layerSelect')).select_by_value('topography')
    driver.execute_script("document.getElementById('layerSelect').dispatchEvent(new Event('change'))")
    WebDriverWait(driver, 25).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, '#table tbody tr')) >= 3)
    time.sleep(1.5)
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    rows = driver.find_elements(By.CSS_SELECTOR, '#table tbody tr')
    logs = driver.get_log('browser')
    severe = [x for x in logs if str(x.get('level','')).upper() == 'SEVERE']
    result.update({
        'status': 'PASS',
        'rendered_rows': len(rows),
        'badge_visible': 'COPERNICUS_ODATA_QUERY_CONTRACT_READY' in body_text,
        'grid_visible': 'N51_W001' in body_text,
        'queue_path_visible': '154_topography_copdem_odata_geocell_sampling_20260711.task.json' in body_text,
        'data_path_visible': 'topography_visible_rows_latest.json' in body_text,
        'status_path_visible': 'topography_visible_status_latest.json' in body_text,
        'console_errors': severe,
        'page_text_sample': body_text[:2000]
    })
finally:
    driver.quit()
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
'@
[System.IO.File]::WriteAllText($tempPy, $pyCode, [System.Text.UTF8Encoding]::new($false))

try {
  if ([System.IO.Path]::GetFileNameWithoutExtension($python) -ieq 'py') {
    & $python -3 $tempPy $tempJson
  } else {
    & $python $tempPy $tempJson
  }
  if ($LASTEXITCODE -ne 0) { throw "SELENIUM_EXIT_CODE_$LASTEXITCODE" }
  if (-not (Test-Path -LiteralPath $tempJson)) { throw 'SELENIUM_RESULT_MISSING' }
  $browser = Get-Content -LiteralPath $tempJson -Raw -Encoding UTF8 | ConvertFrom-Json
} finally {
  Remove-Item -LiteralPath $tempPy -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $tempJson -Force -ErrorAction SilentlyContinue
}

$passed = (
  $staticChecks.html_uses_visible_rows -and
  $staticChecks.html_uses_visible_status -and
  $staticChecks.row_count -ge 3 -and
  $staticChecks.required_badge_rows -ge 3 -and
  $staticChecks.required_grid_rows -ge 3 -and
  $staticChecks.required_queue_rows -ge 3 -and
  [string]$browser.status -eq 'PASS' -and
  [int]$browser.rendered_rows -ge 3 -and
  [bool]$browser.badge_visible -and
  [bool]$browser.grid_visible -and
  [bool]$browser.queue_path_visible -and
  @($browser.console_errors).Count -eq 0
)

$validatedAt = Now-Utc
$proof = [ordered]@{
  task_id = $taskId
  page_key = 'topography'
  status = if ($passed) { 'PASS' } else { 'FAIL' }
  validated_at = $validatedAt
  branch = $branch
  runner_mode = 'single_shared_runner_only'
  canonical_storage = 'F_PORTABLE_ROOT'
  static_checks = $staticChecks
  browser = $browser
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json (Join-Path $repoRoot ($browserProofRel -replace '/', '\')) $proof

$status = [ordered]@{
  task_id = $taskId
  page_key = 'topography'
  status = if ($passed) { 'SITE_VISIBILITY_BROWSER_PASS_NUMERIC_SAMPLING_PENDING' } else { 'SITE_VISIBILITY_VALIDATION_FAILED' }
  validated_at = $validatedAt
  visible_rows_count = $staticChecks.row_count
  browser_rendered_rows = if ($browser.rendered_rows) { [int]$browser.rendered_rows } else { 0 }
  visible_badge_rows = $staticChecks.required_badge_rows
  visible_grid_rows = $staticChecks.required_grid_rows
  height_difference_value_count = $staticChecks.numeric_elevation_rows
  completion_percent = if ($passed) { 45 } else { 40 }
  percent_increase = if ($passed) { 5 } else { 0 }
  next_action = if ($passed) { 'Run task 156 for source-backed EU-DEM fallback samples, then continue primary CopDEM and real parcel-boundary validation.' } else { 'Fix the failed static/browser checks without starting another runner.' }
  blockers = @('numeric_elevation_sampling_pending','real_parcel_boundary_required','primary_copdem_glo30_sampling_required')
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\')) $status
Write-Json (Join-Path $repoRoot ($runnerOutputRel -replace '/', '\')) ([ordered]@{
  task_id=$taskId
  started_at=$startedAt
  completed_at=$validatedAt
  status=if ($passed) { 'COMPLETED_VISIBLE_NOT_FINAL' } else { 'FAILED' }
  browser_proof_path=$browserProofRel
  status_path=$statusRel
  visible_rows_path=$rowsRel
  visible_status_path=$statusWebRel
  final_ready=$false
  fake_data=$false
  db_write=$false
  migration=$false
  production_deploy=$false
})

if (-not $passed) { throw 'TOPOGRAPHY_155_BROWSER_ACCEPTANCE_FAILED' }
Write-Output ($status | ConvertTo-Json -Depth 20)
