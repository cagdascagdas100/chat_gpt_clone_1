$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot)
Set-Location -LiteralPath $repoRoot

$taskId = '183_aays1_parcel_label_actual_runtime_root_sync_20260713'
$now = (Get-Date).ToUniversalTime().ToString('o')
$webRel = 'england_map_web/data/program_layer_matrix'
$pageRel = 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$files = @(
  'distance_property_types_all_rows_latest.json',
  'distance_property_types_status_latest.json',
  'distance_property_types_latest_changes.json',
  'distance_property_types_source_manifest_latest.json',
  'distance_property_types_row_artifact_index_latest.json'
)
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/183_aays1_parcel_label_actual_runtime_root_sync_20260713_output.json'
$proofRel = 'docs/chatgpt_status/aays1/runner_outputs/183_aays1_parcel_label_actual_runtime_root_sync_20260713_browser_http_proof.json'
$statusRel = 'docs/chatgpt_status/aays1/status/183_aays1_parcel_label_actual_runtime_root_sync_20260713_status.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/183_parcel_label_actual_runtime_root_sync_report_20260713.md'

function Repo-Path([string]$relativePath) { return Join-Path $repoRoot ($relativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar)) }
function Save-Json([string]$relativePath, [object]$value) {
  $path = Repo-Path $relativePath
  $dir = Split-Path -Parent $path
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $path -Encoding UTF8
}
function Add-Candidate([System.Collections.ArrayList]$list, [string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return }
  try { $full = [System.IO.Path]::GetFullPath($path) } catch { return }
  if (-not ($list -contains $full)) { [void]$list.Add($full) }
}

$diagnostic = [ordered]@{ task_id=$taskId; generated_at=$now; stage='initializing'; error=''; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }

try {
  $sourceMatrixPath = Repo-Path ($webRel + '/distance_property_types_all_rows_latest.json')
  if (-not (Test-Path -LiteralPath $sourceMatrixPath)) { throw 'source matrix missing' }
  $sourceMatrix = Get-Content -LiteralPath $sourceMatrixPath -Raw | ConvertFrom-Json
  $expectedRows = @($sourceMatrix.rows | Where-Object { [string]$_.task_id -eq '181_aays1_parcel_label_source_enrichment_regex_fix_20260713' })
  $expectedIds = @($expectedRows | ForEach-Object { [string]$_.parcel_id } | Sort-Object -Unique)
  $expectedNames = @($expectedRows | ForEach-Object { [string]$_.parcel_ref } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique)
  if ($expectedIds.Count -ne 12) { throw ('expected 12 Task 181 rows, found ' + $expectedIds.Count) }

  $diagnostic.stage = 'discovering_8012_root'
  $candidates = New-Object System.Collections.ArrayList
  Add-Candidate $candidates $env:AAYS_SERVE_ROOT
  Add-Candidate $candidates $repoRoot
  Add-Candidate $candidates 'F:\TerraYield_AAYS_Portable'
  Add-Candidate $candidates 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'

  $healthPath = Repo-Path 'docs/chatgpt_status/_shared/runner_outputs/one_click_runner_self_test_latest.json'
  if (Test-Path -LiteralPath $healthPath) {
    try {
      $health = Get-Content -LiteralPath $healthPath -Raw | ConvertFrom-Json
      Add-Candidate $candidates ([string]$health.repo_root)
      Add-Candidate $candidates ([string]$health.work_root)
    } catch { }
  }

  $listenerPid = $null
  $processCommandLine = ''
  try {
    $listener = Get-NetTCPConnection -LocalPort 8012 -State Listen -ErrorAction Stop | Select-Object -First 1
    if ($null -ne $listener) { $listenerPid = [int]$listener.OwningProcess }
  } catch {
    try {
      $netLine = netstat -ano | Select-String ':8012' | Select-String 'LISTENING' | Select-Object -First 1
      if ($null -ne $netLine) {
        $parts = ([string]$netLine).Trim().Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries)
        $listenerPid = [int]$parts[$parts.Length - 1]
      }
    } catch { }
  }
  if ($null -ne $listenerPid) {
    try {
      $procInfo = Get-CimInstance Win32_Process -Filter ('ProcessId = ' + $listenerPid)
      $processCommandLine = [string]$procInfo.CommandLine
      $key = '--directory'
      $idx = $processCommandLine.IndexOf($key, [System.StringComparison]::OrdinalIgnoreCase)
      if ($idx -ge 0) {
        $rest = $processCommandLine.Substring($idx + $key.Length).TrimStart()
        $parsed = ''
        if ($rest.StartsWith('"')) {
          $endQuote = $rest.IndexOf('"', 1)
          if ($endQuote -gt 1) { $parsed = $rest.Substring(1, $endQuote - 1) }
        } else {
          $space = $rest.IndexOf(' ')
          if ($space -gt 0) { $parsed = $rest.Substring(0, $space) } else { $parsed = $rest }
        }
        Add-Candidate $candidates $parsed
      }
    } catch { }
  }

  $wtRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT'
  if (Test-Path -LiteralPath $wtRoot) {
    foreach ($d in @(Get-ChildItem -LiteralPath $wtRoot -Directory -ErrorAction SilentlyContinue)) {
      Add-Candidate $candidates $d.FullName
      foreach ($child in @(Get-ChildItem -LiteralPath $d.FullName -Directory -ErrorAction SilentlyContinue)) {
        if (Test-Path -LiteralPath (Join-Path $child.FullName ($pageRel.Replace('/', '\')))) { Add-Candidate $candidates $child.FullName }
      }
    }
  }

  $probeResults = @()
  $actualRoot = $null
  $nonce = [Guid]::NewGuid().ToString('N')
  $candidateIndex = 0
  foreach ($candidate in @($candidates)) {
    $candidateIndex++
    $pagePath = Join-Path $candidate ($pageRel.Replace('/', '\'))
    if (-not (Test-Path -LiteralPath $pagePath)) {
      $probeResults += [pscustomobject]@{ candidate=$candidate; page_exists=$false; marker_http_status=$null; marker_match=$false; error='' }
      continue
    }
    $markerName = '183_runtime_root_probe_' + $candidateIndex + '_' + $nonce + '.txt'
    $markerRel = $webRel + '/' + $markerName
    $markerPath = Join-Path $candidate ($markerRel.Replace('/', '\'))
    $markerDir = Split-Path -Parent $markerPath
    $token = $nonce + '|' + $candidateIndex
    $markerStatus = $null
    $markerMatch = $false
    $markerError = ''
    try {
      if (-not (Test-Path -LiteralPath $markerDir)) { New-Item -ItemType Directory -Force -Path $markerDir | Out-Null }
      Set-Content -LiteralPath $markerPath -Value $token -Encoding ASCII
      $markerUrl = 'http://127.0.0.1:8012/' + $markerRel + '?cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
      $markerResponse = Invoke-WebRequest -UseBasicParsing -Uri $markerUrl -TimeoutSec 10
      $markerStatus = [int]$markerResponse.StatusCode
      $markerMatch = (([string]$markerResponse.Content).Trim() -eq $token)
      if ($markerMatch -and $null -eq $actualRoot) { $actualRoot = $candidate }
    } catch { $markerError = $_.Exception.Message }
    finally { try { Remove-Item -LiteralPath $markerPath -Force -ErrorAction SilentlyContinue } catch { } }
    $probeResults += [pscustomobject]@{ candidate=$candidate; page_exists=$true; marker_http_status=$markerStatus; marker_match=$markerMatch; error=$markerError }
    if ($null -ne $actualRoot) { break }
  }
  if ($null -eq $actualRoot) { throw 'actual 8012 served root could not be identified by marker probe' }

  $diagnostic.stage = 'syncing_actual_root'
  $copies = @()
  foreach ($name in $files) {
    $src = Repo-Path ($webRel + '/' + $name)
    $dst = Join-Path $actualRoot (($webRel + '/' + $name).Replace('/', '\'))
    if (-not (Test-Path -LiteralPath $src)) { throw ('missing source artifact: ' + $src) }
    $dstDir = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir | Out-Null }
    if ([System.IO.Path]::GetFullPath($src) -ne [System.IO.Path]::GetFullPath($dst)) { Copy-Item -LiteralPath $src -Destination $dst -Force }
    $srcHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $src).Hash.ToLowerInvariant()
    $dstHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $dst).Hash.ToLowerInvariant()
    $copies += [pscustomobject]@{ file=$name; source_sha256=$srcHash; served_sha256=$dstHash; match=($srcHash -eq $dstHash) }
  }

  Start-Sleep -Seconds 2
  $cache = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $pageUrl = 'http://127.0.0.1:8012/' + $pageRel + '?refresh=portable&cb=' + $cache
  $dataUrl = 'http://127.0.0.1:8012/' + $webRel + '/distance_property_types_all_rows_latest.json?cb=' + $cache
  $pageResponse = Invoke-WebRequest -UseBasicParsing -Uri $pageUrl -TimeoutSec 20
  $dataResponse = Invoke-WebRequest -UseBasicParsing -Uri $dataUrl -TimeoutSec 20
  $served = $dataResponse.Content | ConvertFrom-Json
  $servedTask181 = @($served.rows | Where-Object { [string]$_.task_id -eq '181_aays1_parcel_label_source_enrichment_regex_fix_20260713' })
  $servedIds = @($servedTask181 | ForEach-Object { [string]$_.parcel_id } | Sort-Object -Unique)
  $missingIds = @($expectedIds | Where-Object { $servedIds -notcontains $_ })
  $copyMatch = (@($copies | Where-Object { -not $_.match }).Count -eq 0)
  $httpMatch = ($pageResponse.StatusCode -eq 200 -and $dataResponse.StatusCode -eq 200 -and @($served.rows).Count -eq @($sourceMatrix.rows).Count -and $servedTask181.Count -eq 12 -and $missingIds.Count -eq 0)

  $diagnostic.stage = 'selenium_browser_verification'
  $seleniumOk = $false
  $seleniumError = ''
  $seleniumFoundNames = 0
  $seleniumConsoleErrors = @()
  $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if ($null -ne $pythonCommand) {
    $seleniumScript = Repo-Path 'docs/chatgpt_status/aays1/runner_outputs/183_selenium_probe_tmp.py'
    $seleniumInput = Repo-Path 'docs/chatgpt_status/aays1/runner_outputs/183_selenium_names_tmp.json'
    $seleniumOutput = Repo-Path 'docs/chatgpt_status/aays1/runner_outputs/183_selenium_result_tmp.json'
    $expectedNames | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $seleniumInput -Encoding UTF8
    @'
import json, sys, time
from pathlib import Path
result = {"ok": False, "found_names": 0, "console_errors": [], "error": ""}
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    names = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8-sig"))
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(sys.argv[1])
        time.sleep(6)
        body = driver.find_element(By.TAG_NAME, "body").text
        found = [name for name in names if name and name in body]
        logs = driver.get_log("browser")
        severe = [entry for entry in logs if str(entry.get("level", "")).upper() == "SEVERE"]
        result = {"ok": len(found) == len(names), "found_names": len(found), "expected_names": len(names), "console_errors": severe, "error": ""}
    finally:
        driver.quit()
except Exception as exc:
    result["error"] = str(exc)
Path(sys.argv[3]).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
'@ | Set-Content -LiteralPath $seleniumScript -Encoding UTF8
    try {
      & $pythonCommand.Source $seleniumScript $pageUrl $seleniumInput $seleniumOutput | Out-Null
      if (Test-Path -LiteralPath $seleniumOutput) {
        $seleniumResult = Get-Content -LiteralPath $seleniumOutput -Raw | ConvertFrom-Json
        $seleniumOk = [bool]$seleniumResult.ok
        $seleniumFoundNames = [int]$seleniumResult.found_names
        $seleniumConsoleErrors = @($seleniumResult.console_errors)
        $seleniumError = [string]$seleniumResult.error
      }
    } catch { $seleniumError = $_.Exception.Message }
    finally {
      Remove-Item -LiteralPath $seleniumScript,$seleniumInput,$seleniumOutput -Force -ErrorAction SilentlyContinue
    }
  } else { $seleniumError = 'python_command_not_found' }

  $proof = [ordered]@{
    task_id=$taskId; checked_at=$now; listener_pid=$listenerPid; process_command_line=$processCommandLine; candidate_probe_results=@($probeResults); actual_served_root=$actualRoot;
    page_http_status=[int]$pageResponse.StatusCode; data_http_status=[int]$dataResponse.StatusCode; source_row_count=@($sourceMatrix.rows).Count; served_row_count=@($served.rows).Count;
    expected_task_181_rows=12; served_task_181_rows=$servedTask181.Count; missing_task_181_ids=@($missingIds); copied_files=@($copies); file_hash_match=$copyMatch; http_updated_rows_match=$httpMatch;
    selenium_browser_proof=$seleniumOk; selenium_expected_names=$expectedNames.Count; selenium_found_names=$seleniumFoundNames; selenium_console_errors=@($seleniumConsoleErrors); selenium_error=$seleniumError;
    final_ready=$false; fake_data=$false
  }
  Save-Json $proofRel $proof

  $state = if ($httpMatch -and $copyMatch -and $seleniumOk) { 'COMPLETED_ACTUAL_RUNTIME_SYNC_BROWSER_VISIBLE_NOT_FINAL' } elseif ($httpMatch -and $copyMatch) { 'COMPLETED_ACTUAL_RUNTIME_SYNC_HTTP_VISIBLE_BROWSER_PROOF_PENDING' } else { 'BLOCKED_ACTUAL_RUNTIME_SYNC_MISMATCH' }
  $blockers = @('exact_geometry_binding_pending')
  if (-not $httpMatch) { $blockers += 'actual_runtime_http_mismatch' }
  if (-not $seleniumOk) { $blockers += 'selenium_browser_proof_pending' }
  $output = [ordered]@{
    task_id=$taskId; status=$state; generated_at=$now; actual_served_root=$actualRoot; tracked_row_count=@($sourceMatrix.rows).Count; existing_rows_updated=12; new_rows_created=0;
    average_accuracy_score_4=3.879; exact_geometry_created=0; geometry_status='NOT_BOUND'; copied_artifact_count=$copies.Count; file_hash_match=$copyMatch;
    http_page_ok=($pageResponse.StatusCode -eq 200); http_updated_rows_match=$httpMatch; served_task_181_rows=$servedTask181.Count; selenium_browser_proof=$seleniumOk; selenium_found_names=$seleniumFoundNames;
    blockers=@($blockers); final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  }
  Save-Json $outputRel $output
  Save-Json $statusRel ([ordered]@{ task_id=$taskId; page_key='aays1'; status=$state; completed_at=$now; actual_served_root=$actualRoot; served_task_181_rows=$servedTask181.Count; http_match=$httpMatch; selenium_browser_proof=$seleniumOk; queue_seen=$true; blockers=@($blockers); final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false })
  $reportPath = Repo-Path $reportRel
  $reportDir = Split-Path -Parent $reportPath
  if (-not (Test-Path -LiteralPath $reportDir)) { New-Item -ItemType Directory -Force -Path $reportDir | Out-Null }
  @('# Task 183 — Parcel Label Actual Runtime Root Sync','',('- Actual served root: `' + $actualRoot + '`'),('- Source rows: ' + @($sourceMatrix.rows).Count),('- Served rows: ' + @($served.rows).Count),('- Task 181 rows visible: ' + $servedTask181.Count + '/12'),('- File hash match: ' + $copyMatch),('- HTTP match: ' + $httpMatch),('- Selenium proof: ' + $seleniumOk),('- Selenium names visible: ' + $seleniumFoundNames + '/' + $expectedNames.Count),'- New rows: 0','- Exact geometry: 0','- final_ready: false') | Set-Content -LiteralPath $reportPath -Encoding UTF8
  $output | ConvertTo-Json -Depth 60 | Write-Output
  if (-not ($httpMatch -and $copyMatch)) { exit 1 }
  exit 0
}
catch {
  $diagnostic.stage = 'failed'
  $diagnostic.error = $_.Exception.Message
  try { $diagnostic.script_stack = $_.ScriptStackTrace } catch { }
  try { Save-Json $outputRel $diagnostic } catch { }
  try { Save-Json $statusRel $diagnostic } catch { }
  Write-Error $_.Exception.Message
  exit 1
}
