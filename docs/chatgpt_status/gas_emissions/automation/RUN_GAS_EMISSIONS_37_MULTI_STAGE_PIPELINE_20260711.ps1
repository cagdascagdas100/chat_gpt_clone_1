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
    (($Value | ConvertTo-Json -Depth 80) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
}
function Get-RowCount([string]$Path) {
  $obj = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
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
  throw 'GAS_EMISSIONS_37_PIPELINE_MUST_RUN_INSIDE_CANONICAL_SHARED_RUNNER'
}
if ($branch -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_37_PIPELINE_WRONG_BRANCH'
}

$portableRoot = 'F:\TerraYield_AAYS_Portable'
$servedRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$rowsRel = 'england_map_web\data\program_layer_matrix\gas_emissions_visible_rows_latest.json'
$statusRel = 'england_map_web\data\program_layer_matrix\gas_emissions_status_latest.json'
$matrixRel = 'england_map_web\TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$candidateRel = 'docs\chatgpt_status\gas_emissions\candidates\151_gas_emissions_official_commercial_2005_candidates_20260711.json'
$gateStatusRel = 'docs\chatgpt_status\gas_emissions\status\150_gas_emissions_8012_publish_and_browser_smoke_28_latest.json'
$v2Rel = 'docs\chatgpt_status\gas_emissions\automation\RUN_GAS_EMISSIONS_28_PUBLISH_AND_BROWSER_SMOKE_20260711_V2.ps1'
$blockerRel = 'docs\chatgpt_status\gas_emissions\status\149_gas_emissions_8012_visibility_blocker_20260711_latest.json'

$rowsPath = Join-Path $repoRoot $rowsRel
$statusPath = Join-Path $repoRoot $statusRel
$matrixPath = Join-Path $repoRoot $matrixRel
$candidatePath = Join-Path $repoRoot $candidateRel
$gateStatusPath = Join-Path $repoRoot $gateStatusRel
$v2Path = Join-Path $repoRoot $v2Rel
$blockerPath = Join-Path $repoRoot $blockerRel
foreach ($p in @($rowsPath,$statusPath,$matrixPath,$candidatePath,$v2Path)) {
  if (-not (Test-Path -LiteralPath $p)) { throw "MISSING_REQUIRED_FILE: $p" }
}

# Stage 1: enforce the existing 28/28 browser gate inside the same runner.
$gatePassed = $false
if (Test-Path -LiteralPath $gateStatusPath) {
  try {
    $gate = Get-Content -LiteralPath $gateStatusPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $gatePassed = ([string]$gate.status -eq 'PASS' -and [int]$gate.unique_row_count -eq 28 -and [int]$gate.new_marker_count -eq 4)
  } catch { $gatePassed = $false }
}
if (-not $gatePassed) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $v2Path
  if ($LASTEXITCODE -ne 0) { throw 'DEPENDENCY_28_BROWSER_GATE_FAILED' }
}
if (-not (Test-Path -LiteralPath $gateStatusPath)) { throw 'DEPENDENCY_28_GATE_OUTPUT_MISSING' }
$gate = Get-Content -LiteralPath $gateStatusPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$gate.status -ne 'PASS' -or [int]$gate.unique_row_count -ne 28) {
  throw 'DEPENDENCY_28_GATE_NOT_PASS'
}

# Stage 2: materialize the official GOV.UK CSV outside the repository.
$sourceDir = Join-Path $portableRoot 'runner_data\gas_emissions\official_sources'
Ensure-Dir $sourceDir
$sourceLocalPath = Join-Path $sourceDir '2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv'
$sourceUrl = 'https://assets.publishing.service.gov.uk/media/68653c7ee6c3cc924228943f/2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv'
if (-not (Test-Path -LiteralPath $sourceLocalPath) -or (Get-Item -LiteralPath $sourceLocalPath).Length -lt 1000000) {
  $tmpDownload = $sourceLocalPath + '.download_' + [Guid]::NewGuid().ToString('N')
  Invoke-WebRequest -Uri $sourceUrl -OutFile $tmpDownload -UseBasicParsing -TimeoutSec 900
  if ((Get-Item -LiteralPath $tmpDownload).Length -lt 1000000) { throw 'OFFICIAL_CSV_DOWNLOAD_TOO_SMALL' }
  Move-Item -LiteralPath $tmpDownload -Destination $sourceLocalPath -Force
}
$sourceInfo = Get-Item -LiteralPath $sourceLocalPath
$sourceSha256 = (Get-FileHash -LiteralPath $sourceLocalPath -Algorithm SHA256).Hash.ToLowerInvariant()

# Only the first Hartlepool section is needed; avoid loading the 79 MB file fully.
$headLines = @([System.IO.File]::ReadLines($sourceLocalPath) | Select-Object -First 260)
$csvRows = @($headLines | ConvertFrom-Csv)
$candidateManifest = Get-Content -LiteralPath $candidatePath -Raw -Encoding UTF8 | ConvertFrom-Json
$verified = New-Object System.Collections.Generic.List[object]
foreach ($candidate in @($candidateManifest.candidates)) {
  $match = @($csvRows | Where-Object {
    [string]$_.'Local Authority Code' -eq 'E06000001' -and
    [int]$_.'Calendar Year' -eq 2005 -and
    [string]$_.'LA GHG Sector' -eq 'Commercial' -and
    [string]$_.'LA GHG Sub-sector' -eq [string]$candidate.sub_sector -and
    [string]$_.'Greenhouse gas' -eq [string]$candidate.greenhouse_gas
  })
  if ($match.Count -ne 1) { throw "OFFICIAL_CSV_MATCH_COUNT_NOT_ONE: $($candidate.row_id) count=$($match.Count)" }
  $m = $match[0]
  $actualTerritorial = [double]$_ = [double]$m.'Territorial emissions (kt CO2e)'
  $actualScope = [double]$m.'Emissions within the scope of influence of LAs (kt CO2)'
  if ([Math]::Abs($actualTerritorial - [double]$candidate.territorial_emissions_kt_co2e) -gt 0.000000001) {
    throw "TERRITORIAL_VALUE_MISMATCH: $($candidate.row_id)"
  }
  if ([Math]::Abs($actualScope - [double]$candidate.scope_of_influence_kt_co2) -gt 0.000000001) {
    throw "SCOPE_VALUE_MISMATCH: $($candidate.row_id)"
  }
  $verified.Add([ordered]@{
    row_id = [string]$candidate.row_id
    calendar_year = 2005
    sector = 'Commercial'
    sub_sector = [string]$candidate.sub_sector
    greenhouse_gas = [string]$candidate.greenhouse_gas
    territorial_emissions_kt_co2e = $actualTerritorial
    scope_of_influence_kt_co2 = $actualScope
    source_lines = [string]$candidate.source_preview_line
    matching_method = 'official_govuk_preview_plus_downloaded_csv_exact_fields'
    calculation_explanation = "Official GOV.UK preview $($candidate.source_preview_line) and downloaded CSV exact-key/value match; no parcel allocation or derived calculation applied."
    confidence_percent = 94
    accuracy_score_4 = '3.4/4'
    needs_manual_review = $true
    parcel_binding_status = 'PENDING'
    source_url = [string]$candidateManifest.source_page_url
    source_download_url = $sourceUrl
    source_local_raw_path = $sourceLocalPath
    source_local_sha256 = $sourceSha256
    source_manifest_path = ($candidateRel -replace '\\','/')
    source_path = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
    visible_rows_artifact_path = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
    status_path = 'england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
    report_path = 'docs/chatgpt_status/gas_emissions/reports/151_gas_emissions_official_csv_dual_match_and_37_browser_smoke_20260711.json'
    changed_in_latest_run = $true
    is_new_in_latest_batch = $true
    display_badge = 'KAYNAKLI_YENI'
    served_commit_sha = 'PENDING_RUNNER_COMMIT'
    artifact_sha = 'SEE_STATUS_ARTIFACT_SHA256'
  })
}
if ($verified.Count -ne 9) { throw "VERIFIED_CANDIDATE_COUNT_NOT_9: $($verified.Count)" }

# Stage 3: expand 28 -> 37 only after the browser gate passed.
$visible = Get-Content -LiteralPath $rowsPath -Raw -Encoding UTF8 | ConvertFrom-Json
$existing = @($visible.rows)
if ($existing.Count -ne 28 -and $existing.Count -ne 37) { throw "UNEXPECTED_VISIBLE_ROW_COUNT: $($existing.Count)" }
$targetIds = @($verified | ForEach-Object { [string]$_.row_id })
$oldRows = @($existing | Where-Object { $targetIds -notcontains [string]$_.row_id })
foreach ($row in $oldRows) {
  $row.changed_in_latest_run = $false
  $row.is_new_in_latest_batch = $false
  $row.display_badge = 'KAYNAKLI_MEVCUT'
  $row.source_local_raw_path = $sourceLocalPath
  $row | Add-Member -NotePropertyName source_local_sha256 -NotePropertyValue $sourceSha256 -Force
  $row | Add-Member -NotePropertyName source_manifest_path -NotePropertyValue ($candidateRel -replace '\\','/') -Force
}
$visible.rows = @($oldRows) + @($verified)
$visible.status = 'OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_37'
$visible.previous_visible_row_count = 28
$visible.previous_visible_rows_count = 28
$visible.new_rows_added_this_run = 9
$visible.new_rows_in_latest_batch = 9
$visible.visible_row_count = 37
$visible.visible_rows_count = 37
$visible.latest_batch_id = 'gas_emissions_official_commercial_2005_20260711_01'
$visible.source_row_accuracy_score_4 = '3.4/4'
$visible.accuracy_note = '37 official GOV.UK rows; the latest nine passed preview-line plus downloaded-CSV exact-value checks. Parcel binding remains pending.'
$visible.browser_smoke_passed_for_28_rows = $true
$visible | Add-Member -NotePropertyName browser_smoke_passed_for_37_rows -NotePropertyValue $false -Force
$visible.source_local_raw_path = $sourceLocalPath
$visible | Add-Member -NotePropertyName source_local_sha256 -NotePropertyValue $sourceSha256 -Force
$visible.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$visible.final_ready = $false
$visible.product_final_ready = $false
$visible.fake_data = $false
$visible.db_write = $false
$visible.migration = $false
$visible.production_deploy = $false
Write-Json $rowsPath $visible

$artifactSha256 = (Get-FileHash -LiteralPath $rowsPath -Algorithm SHA256).Hash.ToLowerInvariant()
$status = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
$status.status = 'OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_37'
$status.previous_visible_row_count = 28
$status.previous_visible_rows_count = 28
$status.new_rows_added_this_run = 9
$status.new_rows_in_latest_batch = 9
$status.current_visible_change_rows = 9
$status.visible_rows_count = 37
$status.verification_score_after = '3.4/4'
$status.accuracy_ge_3_count_this_run = 9
$status.source_local_raw_path = $sourceLocalPath
$status | Add-Member -NotePropertyName source_local_sha256 -NotePropertyValue $sourceSha256 -Force
$status | Add-Member -NotePropertyName source_local_size_bytes -NotePropertyValue ([int64]$sourceInfo.Length) -Force
$status | Add-Member -NotePropertyName artifact_sha256 -NotePropertyValue $artifactSha256 -Force
$status.browser_smoke_passed = $false
$status.next_required_runner_action = 'Run 37-row browser smoke, then continue parcel-level matching without inventing allocation or geometry.'
$status.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$status.final_ready = $false
$status.product_final_ready = $false
$status.fake_data = $false
$status.db_write = $false
$status.migration = $false
$status.production_deploy = $false
Write-Json $statusPath $status

# Stage 4: publish to the fixed 8012 root and prove all 37 rows in Chrome/Selenium.
foreach ($rel in @($rowsRel,$statusRel,$matrixRel)) {
  Copy-Atomic (Join-Path $repoRoot $rel) (Join-Path $servedRoot $rel)
}
$httpUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json?gas37=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$httpCount = -1
for ($i=0; $i -lt 15; $i++) {
  try { $httpCount = @((Invoke-RestMethod -Uri $httpUrl -TimeoutSec 20 -Headers @{'Cache-Control'='no-cache'}).rows).Count } catch {}
  if ($httpCount -eq 37) { break }
  Start-Sleep -Seconds 2
}
if ($httpCount -ne 37) { throw "HTTP_8012_ROW_COUNT_NOT_37: $httpCount" }

$tmpBase = Join-Path ([System.IO.Path]::GetTempPath()) $taskId
$tmpPy = $tmpBase + '.py'
$tmpOut = $tmpBase + '.json'
$pySource = @'
import json, sys, time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select

out_path = Path(sys.argv[1])
url = "http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=gas37&ts=" + str(int(time.time()))
expected = {
"GHG-HPL-2005-commercial-electricity-co2","GHG-HPL-2005-commercial-electricity-ch4","GHG-HPL-2005-commercial-electricity-n2o",
"GHG-HPL-2005-commercial-gas-co2","GHG-HPL-2005-commercial-gas-ch4","GHG-HPL-2005-commercial-gas-n2o",
"GHG-HPL-2005-commercial-other-co2","GHG-HPL-2005-commercial-other-ch4","GHG-HPL-2005-commercial-other-n2o"}
result={"status":"FAIL","url":url,"unique_row_count":0,"new_marker_count":0,"manual_marker_count":0,"console_errors":[],"error":None}
driver=None
try:
    options=webdriver.ChromeOptions()
    options.add_argument("--headless=new"); options.add_argument("--disable-gpu"); options.add_argument("--no-sandbox"); options.add_argument("--disable-dev-shm-usage"); options.add_argument("--window-size=1920,1400")
    options.set_capability("goog:loggingPrefs", {"browser":"ALL"})
    driver=webdriver.Chrome(options=options); driver.get(url)
    wait=WebDriverWait(driver,45); wait.until(lambda d:d.find_element(By.ID,"layerSelect"))
    Select(driver.find_element(By.ID,"layerSelect")).select_by_value("gas")
    wait.until(lambda d:"37 satır" in d.find_element(By.ID,"pageInfo").text)
    rows={}
    def collect():
        for tr in driver.find_elements(By.CSS_SELECTOR,"#table tbody tr"):
            td=tr.find_elements(By.TAG_NAME,"td")
            if len(td)>1 and td[1].text.strip(): rows[td[1].text.strip()]=td[0].text.strip()
    collect()
    while "Sayfa 2 / 2" not in driver.find_element(By.ID,"pageInfo").text:
        driver.find_element(By.ID,"next").click(); wait.until(lambda d:"Sayfa 2 / 2" in d.find_element(By.ID,"pageInfo").text)
    collect()
    severe=[]
    try: severe=[e for e in driver.get_log("browser") if str(e.get("level","")).upper()=="SEVERE"]
    except Exception: severe=[]
    present=expected.issubset(rows.keys())
    new_count=sum(1 for rid in expected if "YENİ / LATEST" in rows.get(rid,""))
    manual_count=sum(1 for rid in expected if "MANUEL İNCELEME" in rows.get(rid,""))
    passed=len(rows)==37 and present and new_count==9 and manual_count==9 and not severe
    result.update({"status":"PASS" if passed else "FAIL","unique_row_count":len(rows),"rendered_row_ids":sorted(rows),"expected_new_rows_present":present,"new_marker_count":new_count,"manual_marker_count":manual_count,"page_info":driver.find_element(By.ID,"pageInfo").text,"console_errors":severe})
    if not passed: result["error"]="row_count_expected_ids_markers_or_console_failed"
except Exception as exc: result["error"]=f"{type(exc).__name__}: {exc}"
finally:
    if driver:
        try: driver.quit()
        except Exception: pass
    out_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
sys.exit(0 if result["status"]=="PASS" else 1)
'@
[System.IO.File]::WriteAllText($tmpPy,$pySource,[System.Text.UTF8Encoding]::new($false))
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) { & $python.Source $tmpPy $tmpOut } else { & (Get-Command py -ErrorAction Stop).Source -3 $tmpPy $tmpOut }
$browserExit = $LASTEXITCODE
$browser = Get-Content -LiteralPath $tmpOut -Raw -Encoding UTF8 | ConvertFrom-Json
$browserPassed = ($browserExit -eq 0 -and [string]$browser.status -eq 'PASS' -and [int]$browser.unique_row_count -eq 37 -and [int]$browser.new_marker_count -eq 9)

$reportRel = 'docs/chatgpt_status/gas_emissions/reports/151_gas_emissions_official_csv_dual_match_and_37_browser_smoke_20260711.json'
$reportPath = Join-Path $repoRoot ($reportRel -replace '/','\')
$statusOutRel = 'docs/chatgpt_status/gas_emissions/status/151_gas_emissions_official_csv_dual_match_and_37_browser_smoke_latest.json'
$statusOutPath = Join-Path $repoRoot ($statusOutRel -replace '/','\')
$payload = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  status = if ($browserPassed) { 'PASS' } else { 'FAIL' }
  generated_by_runner = $true
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  source = [string]$candidateManifest.source
  source_page_url = [string]$candidateManifest.source_page_url
  source_download_url = $sourceUrl
  source_local_raw_path = $sourceLocalPath
  source_local_size_bytes = [int64]$sourceInfo.Length
  source_local_sha256 = $sourceSha256
  candidate_count = 9
  csv_exact_match_count = $verified.Count
  previous_visible_rows = 28
  current_visible_rows = 37
  served_http_row_count = $httpCount
  browser_status = [string]$browser.status
  browser_unique_row_count = [int]$browser.unique_row_count
  browser_new_marker_count = [int]$browser.new_marker_count
  browser_manual_marker_count = [int]$browser.manual_marker_count
  browser_console_errors = @($browser.console_errors)
  artifact_sha256 = $artifactSha256
  source_accuracy_score_4 = '3.4/4'
  confidence_percent = 94
  parcel_binding_gate_passed = $false
  single_runner_only = $true
  new_runner = $false
  parallel_runner = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  git_push_status = 'pending_runner_wrapper'
}
Write-Json $reportPath $payload
Write-Json $statusOutPath $payload

if ($browserPassed) {
  $status.browser_smoke_passed = $true
  $status | Add-Member -NotePropertyName browser_smoke_row_count -NotePropertyValue 37 -Force
  $status | Add-Member -NotePropertyName browser_smoke_new_marker_count -NotePropertyValue 9 -Force
  $status | Add-Member -NotePropertyName browser_smoke_report_path -NotePropertyValue $reportRel -Force
  $status | Add-Member -NotePropertyName browser_smoke_passed_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
  $status.next_required_runner_action = 'Proceed to parcel-level binding and required popup/legend field coverage; do not infer parcel emissions from authority totals.'
  Write-Json $statusPath $status
  Copy-Atomic $statusPath (Join-Path $servedRoot $statusRel)
}

# Stage 5: perform a non-destructive parcel/UI readiness audit in the same task.
$geoRel = 'england_map_web\data\parcel_emissions_scores.geojson'
$appRel = 'england_map_web\app.js'
$geoPath = Join-Path $repoRoot $geoRel
$appPath = Join-Path $repoRoot $appRel
$requiredFields = @('emission_percent','level','risk_color','confidence','source','source_date','matching_method','calculation_explanation')
$featureCount = 0
$completeFeatureCount = 0
$missingCounts = [ordered]@{}
foreach ($field in $requiredFields) { $missingCounts[$field] = 0 }
if (Test-Path -LiteralPath $geoPath) {
  $geo = Get-Content -LiteralPath $geoPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $features = @($geo.features)
  $featureCount = $features.Count
  foreach ($feature in $features) {
    $complete = $true
    foreach ($field in $requiredFields) {
      $value = $feature.properties.$field
      if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) { $missingCounts[$field]++; $complete = $false }
    }
    if ($complete) { $completeFeatureCount++ }
  }
}
$appText = if (Test-Path -LiteralPath $appPath) { Get-Content -LiteralPath $appPath -Raw -Encoding UTF8 } else { '' }
$uiChecks = [ordered]@{
  air_icon_reference = $appText -match 'air\.png'
  emission_percent_reference = $appText -match 'emission_percent'
  risk_color_reference = $appText -match 'risk_color'
  confidence_reference = $appText -match 'confidence'
  source_date_reference = $appText -match 'source_date'
  matching_method_reference = $appText -match 'matching_method'
  calculation_explanation_reference = $appText -match 'calculation_explanation'
  legend_reference = $appText -match 'legend'
}
$auditPassed = ($featureCount -gt 0 -and $completeFeatureCount -eq $featureCount -and (@($uiChecks.Values | Where-Object { -not $_ }).Count -eq 0))
$auditRel = 'docs/chatgpt_status/gas_emissions/status/152_gas_emissions_parcel_binding_ui_readiness_audit_latest.json'
$auditPath = Join-Path $repoRoot ($auditRel -replace '/','\')
$audit = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  status = if ($auditPassed) { 'PASS_STATIC_READINESS' } else { 'BLOCKED_MISSING_PARCEL_OR_UI_FIELDS' }
  generated_by_runner = $true
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  geojson_path = ($geoRel -replace '\\','/')
  geojson_feature_count = $featureCount
  complete_required_field_feature_count = $completeFeatureCount
  required_fields = $requiredFields
  missing_field_counts = $missingCounts
  ui_checks = $uiChecks
  browser_rows_passed = $browserPassed
  parcel_binding_gate_passed = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json $auditPath $audit

Remove-Item -LiteralPath $tmpPy,$tmpOut -Force -ErrorAction SilentlyContinue
if (-not $browserPassed) { throw 'GAS_EMISSIONS_37_BROWSER_SMOKE_FAILED' }
Write-Output ($payload | ConvertTo-Json -Depth 80)
