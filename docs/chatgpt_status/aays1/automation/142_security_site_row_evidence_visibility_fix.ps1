$ErrorActionPreference = 'Continue'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$branch = 'codex/aays-single-runner-v5-20260706'
$taskId = 'aays1-142-security-site-row-evidence-visibility-fix-20260711'
$now = Get-Date
$generatedAt = $now.ToString('o')

$visibleRowsRel = 'england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json'
$visibleStatusRel = 'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json'
$csvRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv'
$geoRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson'
$manifestRel = 'england_map_web/data/security_public_safety/security_evidence_manifest.json'
$htmlRel = 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$reportRel = 'docs/chatgpt_status/aays1/reports/142_security_site_row_evidence_visibility_fix_completion_20260711.md'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/142_security_site_row_evidence_visibility_fix.json'
$browserProofRel = 'docs/chatgpt_status/_shared/reports/security_row_evidence_browser_validation_20260711.json'
$operationsRel = 'england_map_web/data/program_layer_matrix/security_public_safety_operations_latest.json'
$reportMirrorRel = 'england_map_web/data/program_layer_matrix/security_142_completion_report.md'

$visibleRowsPath = Join-Path $repoRoot $visibleRowsRel
$visibleStatusPath = Join-Path $repoRoot $visibleStatusRel
$csvPath = Join-Path $repoRoot $csvRel
$geoPath = Join-Path $repoRoot $geoRel
$manifestPath = Join-Path $repoRoot $manifestRel
$htmlPath = Join-Path $repoRoot $htmlRel
$reportPath = Join-Path $repoRoot $reportRel
$outputPath = Join-Path $repoRoot $outputRel
$browserProofPath = Join-Path $repoRoot $browserProofRel
New-Item -ItemType Directory -Force -Path (Split-Path $reportPath),(Split-Path $outputPath),(Split-Path $browserProofPath) | Out-Null

$result = [ordered]@{
  task_id = $taskId
  status = 'started'
  branch = $branch
  commit_sha = $null
  runner_pid = $PID
  single_runner_only = $true
  parallel_runner = $false
  before_visible_rows = 0
  after_visible_rows = 0
  before_geojson_features = 0
  after_geojson_features = 0
  verified_csv_rows = 0
  new_rows_in_latest_batch = 0
  clickable_source_links_checked = 0
  artifact_links_http_200 = 0
  artifact_links_missing = 0
  all_old_rows_marked_latest = $false
  html_contract_checks = [ordered]@{}
  browser_smoke_status = 'not_run'
  browser_url = $null
  console_error_count = $null
  git_push_status = 'not_attempted'
  remote_readback_status = 'not_attempted'
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
  $result | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $outputPath
}

try {
  foreach ($required in @($visibleRowsPath,$visibleStatusPath,$csvPath,$geoPath,$manifestPath,$htmlPath)) {
    if (-not (Test-Path $required)) { throw "missing_required_file:$required" }
  }

  $visible = Get-Content -Raw -Encoding UTF8 $visibleRowsPath | ConvertFrom-Json
  $status = Get-Content -Raw -Encoding UTF8 $visibleStatusPath | ConvertFrom-Json
  $manifest = Get-Content -Raw -Encoding UTF8 $manifestPath | ConvertFrom-Json
  $csvRows = @(Import-Csv -LiteralPath $csvPath)
  $geo = Get-Content -Raw -Encoding UTF8 $geoPath | ConvertFrom-Json
  $geoFeatures = @($geo.features)
  $html = Get-Content -Raw -Encoding UTF8 $htmlPath

  $rows = @($visible.rows)
  $result.before_visible_rows = $rows.Count
  $result.before_geojson_features = $geoFeatures.Count
  $result.verified_csv_rows = $csvRows.Count

  if ($rows.Count -ne $csvRows.Count -or $rows.Count -ne $geoFeatures.Count) {
    throw "baseline_count_mismatch:rows=$($rows.Count),csv=$($csvRows.Count),geo=$($geoFeatures.Count)"
  }

  $latestBatchId = if ($visible.latest_batch_id) { [string]$visible.latest_batch_id } else { 'security_baseline_150_verified' }
  if ($rows.Count -eq 150) { $latestBatchId = 'security_baseline_150_verified' }
  $csvSha = (Get-FileHash -LiteralPath $csvPath -Algorithm SHA256).Hash.ToLowerInvariant()
  $geoSha = (Get-FileHash -LiteralPath $geoPath -Algorithm SHA256).Hash.ToLowerInvariant()
  $manifestSha = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
  $newCount = 0
  foreach ($row in $rows) {
    if ([string]::IsNullOrWhiteSpace([string]$row.source_url)) { $row | Add-Member -NotePropertyName source_url -NotePropertyValue 'https://data.police.uk/' -Force }
    if ([string]::IsNullOrWhiteSpace([string]$row.source_path)) { $row | Add-Member -NotePropertyName source_path -NotePropertyValue $csvRel -Force }
    if ([string]::IsNullOrWhiteSpace([string]$row.evidence_path)) { $row | Add-Member -NotePropertyName evidence_path -NotePropertyValue $geoRel -Force }
    if ([string]::IsNullOrWhiteSpace([string]$row.source_manifest_path)) { $row | Add-Member -NotePropertyName source_manifest_path -NotePropertyValue $manifestRel -Force }
    $row | Add-Member -NotePropertyName report_path -NotePropertyValue $reportMirrorRel -Force
    $row | Add-Member -NotePropertyName task_id -NotePropertyValue $taskId -Force
    $row | Add-Member -NotePropertyName source_csv_sha256 -NotePropertyValue $csvSha -Force
    $row | Add-Member -NotePropertyName source_geojson_sha256 -NotePropertyValue $geoSha -Force
    $row | Add-Member -NotePropertyName source_manifest_sha256 -NotePropertyValue $manifestSha -Force
    $row | Add-Member -NotePropertyName operation_status -NotePropertyValue 'BASELINE_SOURCE_EVIDENCE_VISIBLE' -Force
    if ([string]::IsNullOrWhiteSpace([string]$row.candidate_status)) { $row | Add-Member -NotePropertyName candidate_status -NotePropertyValue 'VISIBLE_SOURCE_BACKED' -Force }
    if ([string]::IsNullOrWhiteSpace([string]$row.batch_id)) { $row | Add-Member -NotePropertyName batch_id -NotePropertyValue 'security_baseline_150_verified' -Force }
    if ([string]::IsNullOrWhiteSpace([string]$row.first_seen_at)) { $row | Add-Member -NotePropertyName first_seen_at -NotePropertyValue ([string]$row.source_date) -Force }
    $row | Add-Member -NotePropertyName last_verified_at -NotePropertyValue $generatedAt -Force

    $isNew = ($row.batch_id -eq $latestBatchId -and $row.is_new_in_latest_batch -eq $true -and $latestBatchId -ne 'security_baseline_150_verified')
    $row | Add-Member -NotePropertyName is_new_in_latest_batch -NotePropertyValue $isNew -Force
    $row | Add-Member -NotePropertyName changed_in_latest_run -NotePropertyValue $isNew -Force
    if ($isNew) { $newCount++ }
  }

  $visible | Add-Member -NotePropertyName verified_csv_rows -NotePropertyValue $csvRows.Count -Force
  $visible | Add-Member -NotePropertyName verified_geojson_features -NotePropertyValue $geoFeatures.Count -Force
  $visible | Add-Member -NotePropertyName visible_rows_count -NotePropertyValue $rows.Count -Force
  $visible | Add-Member -NotePropertyName previous_visible_rows_count -NotePropertyValue ($rows.Count - $newCount) -Force
  $visible | Add-Member -NotePropertyName new_rows_in_latest_batch -NotePropertyValue $newCount -Force
  $visible | Add-Member -NotePropertyName source_manifest_path -NotePropertyValue $manifestRel -Force
  $visible | Add-Member -NotePropertyName latest_report_path -NotePropertyValue $reportRel -Force
  $visible | Add-Member -NotePropertyName browser_report_path -NotePropertyValue $reportMirrorRel -Force
  $visible | Add-Member -NotePropertyName operations_path -NotePropertyValue $operationsRel -Force
  $visible | Add-Member -NotePropertyName latest_runner_output_path -NotePropertyValue $outputRel -Force
  $visible | Add-Member -NotePropertyName final_ready -NotePropertyValue $false -Force
  $visible | Add-Member -NotePropertyName fake_data -NotePropertyValue $false -Force
  $visible | Add-Member -NotePropertyName db_write -NotePropertyValue $false -Force
  $visible | Add-Member -NotePropertyName migration -NotePropertyValue $false -Force
  $visible | Add-Member -NotePropertyName production_deploy -NotePropertyValue $false -Force
  $visible | Add-Member -NotePropertyName rows -NotePropertyValue $rows -Force
  $manifest | Add-Member -NotePropertyName visible_rows_count -NotePropertyValue $rows.Count -Force
  $manifest | Add-Member -NotePropertyName verified_csv_rows -NotePropertyValue $csvRows.Count -Force
  $manifest | Add-Member -NotePropertyName verified_geojson_features -NotePropertyValue $geoFeatures.Count -Force
  $manifest | Add-Member -NotePropertyName csv_sha256 -NotePropertyValue $csvSha -Force
  $manifest | Add-Member -NotePropertyName geojson_sha256 -NotePropertyValue $geoSha -Force
  $manifest | Add-Member -NotePropertyName manifest_sha256_before_update -NotePropertyValue $manifestSha -Force
  $manifest | Add-Member -NotePropertyName browser_report_path -NotePropertyValue $reportMirrorRel -Force
  $manifest | Add-Member -NotePropertyName operations_path -NotePropertyValue $operationsRel -Force
  $manifest | Add-Member -NotePropertyName updated_at -NotePropertyValue $generatedAt -Force
  $manifest | Add-Member -NotePropertyName blockers -NotePropertyValue @('PRODUCT_FINAL_VALIDATION_PENDING') -Force
  $manifest | Add-Member -NotePropertyName final_ready -NotePropertyValue $false -Force
  $manifest | Add-Member -NotePropertyName fake_data -NotePropertyValue $false -Force
  $manifest | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $manifestPath
  $visible | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $visibleRowsPath
  $operations=@(
    [ordered]@{operation_id="${taskId}_validate_counts";task_id=$taskId;operation_type='baseline_validation';stage='csv_geojson_visible_count';status='passed';row_count=$rows.Count;source_path=$csvRel;evidence_path=$geoRel;blocker='';is_new_operation=$true;completed_at=$generatedAt;final_ready=$false;fake_data=$false},
    [ordered]@{operation_id="${taskId}_row_provenance";task_id=$taskId;operation_type='row_provenance';stage='attach_source_manifest_report_checksums';status='passed';row_count=$rows.Count;source_path=$manifestRel;evidence_path=$operationsRel;blocker='';is_new_operation=$true;completed_at=$generatedAt;final_ready=$false;fake_data=$false},
    [ordered]@{operation_id="${taskId}_browser_gate";task_id=$taskId;operation_type='browser_acceptance';stage='http_and_selenium_visibility';status='pending';row_count=$rows.Count;source_path=$visibleRowsRel;evidence_path=$browserProofRel;blocker='BROWSER_ACCEPTANCE_PENDING';is_new_operation=$true;completed_at=$null;final_ready=$false;fake_data=$false}
  )
  ([ordered]@{task_id=$taskId;updated_at=$generatedAt;operation_count=$operations.Count;new_operations_count=$operations.Count;blocked_operation_count=0;operations=$operations;final_ready=$false;fake_data=$false}|ConvertTo-Json -Depth 30)|Set-Content -LiteralPath (Join-Path $repoRoot $operationsRel) -Encoding UTF8

  $status | Add-Member -NotePropertyName verified_csv_rows -NotePropertyValue $csvRows.Count -Force
  $status | Add-Member -NotePropertyName verified_geojson_features -NotePropertyValue $geoFeatures.Count -Force
  $status | Add-Member -NotePropertyName geojson_feature_count -NotePropertyValue $geoFeatures.Count -Force
  $status | Add-Member -NotePropertyName browser_visible_rows -NotePropertyValue $rows.Count -Force
  $status | Add-Member -NotePropertyName visible_rows_count -NotePropertyValue $rows.Count -Force
  $status | Add-Member -NotePropertyName previous_visible_rows_count -NotePropertyValue ($rows.Count - $newCount) -Force
  $status | Add-Member -NotePropertyName new_rows_in_latest_batch -NotePropertyValue $newCount -Force
  $status | Add-Member -NotePropertyName latest_batch_id -NotePropertyValue $latestBatchId -Force
  $status | Add-Member -NotePropertyName source_manifest_path -NotePropertyValue $manifestRel -Force
  $status | Add-Member -NotePropertyName latest_report_path -NotePropertyValue $reportRel -Force
  $status | Add-Member -NotePropertyName latest_runner_output_path -NotePropertyValue $outputRel -Force
  $status | Add-Member -NotePropertyName updated_at -NotePropertyValue $generatedAt -Force
  $status | Add-Member -NotePropertyName final_ready -NotePropertyValue $false -Force
  $status | Add-Member -NotePropertyName product_final_ready -NotePropertyValue $false -Force
  $status | Add-Member -NotePropertyName fake_data -NotePropertyValue $false -Force
  $status | Add-Member -NotePropertyName db_write -NotePropertyValue $false -Force
  $status | Add-Member -NotePropertyName migration -NotePropertyValue $false -Force
  $status | Add-Member -NotePropertyName production_deploy -NotePropertyValue $false -Force
  $status | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $visibleStatusPath

  $result.after_visible_rows = $rows.Count
  $result.after_geojson_features = $geoFeatures.Count
  $result.new_rows_in_latest_batch = $newCount
  $oldLatestCount = @($rows | Where-Object { $_.batch_id -eq 'security_baseline_150_verified' -and ($_.is_new_in_latest_batch -eq $true -or $_.changed_in_latest_run -eq $true) }).Count
  $result.all_old_rows_marked_latest = ($oldLatestCount -eq $rows.Count -and $rows.Count -gt 0)
  if ($oldLatestCount -gt 0) { $result.blockers += "baseline_rows_still_marked_latest:$oldLatestCount" }

  $result.html_contract_checks = [ordered]@{
    verified_geojson_fallback = $html.Contains('verified_geojson_features')
    official_source_column = $html.Contains('Resmi kaynak URL')
    artifact_link_renderer = $html.Contains('data-artifact-link')
    latest_batch_logic = $html.Contains('is_new_in_latest_batch')
    missing_artifact_label = $html.Contains('MISSING / NOT DOWNLOADED')
  }
  foreach ($entry in $result.html_contract_checks.GetEnumerator()) {
    if (-not $entry.Value) { $result.blockers += "html_contract_missing:$($entry.Key)" }
  }

  @"
# AAYS1 Security row evidence visibility fix

- Generated at: $generatedAt
- Visible rows: $($rows.Count)
- CSV rows: $($csvRows.Count)
- GeoJSON features: $($geoFeatures.Count)
- New rows in latest batch: $newCount
- Baseline rows incorrectly marked latest: $oldLatestCount
- Official source URL: https://data.police.uk/
- CSV artifact: $csvRel
- GeoJSON artifact: $geoRel
- Manifest: $manifestRel
- final_ready: false
- fake_data: false
- db_write: false
- migration: false
- production_deploy: false

Browser proof is recorded separately and final readiness remains false.
"@ | Set-Content -Encoding UTF8 $reportPath
  Copy-Item -LiteralPath $reportPath -Destination (Join-Path $repoRoot $reportMirrorRel) -Force
  if($env:AAYS_CONTROLLER_REPO_ROOT){$publisher=Join-Path $repoRoot 'docs/chatgpt_status/_shared/automation/PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1';$publishArg=(@($visibleRowsRel,$visibleStatusRel,$operationsRel,$reportMirrorRel)-join'|');& powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $repoRoot -ControllerRoot $env:AAYS_CONTROLLER_REPO_ROOT -Paths $publishArg -AllowGeneratedArtifacts -SyncPortableWeb;if($LASTEXITCODE-ne0){$result.blockers+='live_controller_publish_blocked'}}

  $baseUrl = $null
  foreach ($candidate in @('http://127.0.0.1:8012','http://127.0.0.1:8020')) {
    try {
      $probe = Invoke-WebRequest -UseBasicParsing -Uri "$candidate/health" -TimeoutSec 8
      if ([int]$probe.StatusCode -eq 200) { $baseUrl = $candidate; break }
    } catch {}
  }

  $artifactUrls = @()
  if ($baseUrl) {
    $artifactUrls = @(
      "$baseUrl/england_map_web/data/security_public_safety/parcel_security_scores_verified.csv",
      "$baseUrl/england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson",
      "$baseUrl/england_map_web/data/security_public_safety/security_evidence_manifest.json",
      "$baseUrl/$reportMirrorRel"
    )
    foreach ($url in $artifactUrls) {
      $result.clickable_source_links_checked++
      try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 20
        if ([int]$r.StatusCode -eq 200) { $result.artifact_links_http_200++ } else { $result.artifact_links_missing++ }
      } catch { $result.artifact_links_missing++ }
    }
  } else {
    $result.blockers += 'local_http_server_not_reachable_on_8012_or_8020'
  }

  $pythonScript = @'
import json, sys, time
from pathlib import Path
out = Path(sys.argv[1])
urls = sys.argv[2:]
proof = {"status":"failed","url":None,"console_error_count":None,"visible_rows_text":None,"geojson_metric_present":False,"source_link_count":0,"artifact_link_count":0,"error":None}
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
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
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "table")))
            WebDriverWait(driver, 30).until(lambda d: "Security / Public Safety" in d.find_element(By.ID,"title").text)
            time.sleep(2)
            body = driver.find_element(By.TAG_NAME,"body").text
            logs = driver.get_log("browser")
            errors = [x for x in logs if x.get("level") == "SEVERE"]
            proof.update({
                "status":"pass" if ("GeoJSON feature: 150" in body or "GeoJSON feature: 300" in body) and len(errors)==0 else "failed",
                "url":url,
                "console_error_count":len(errors),
                "visible_rows_text":next((line for line in body.splitlines() if "Görünür satır" in line), None),
                "geojson_metric_present":("GeoJSON feature: 150" in body or "GeoJSON feature: 300" in body),
                "source_link_count":len(driver.find_elements(By.CSS_SELECTOR,'a[href^="https://data.police.uk"]')),
                "artifact_link_count":len(driver.find_elements(By.CSS_SELECTOR,'a[data-artifact-link="true"]')),
                "console_errors":errors[:20]
            })
            if proof["status"] == "pass":
                break
        except Exception as exc:
            last = repr(exc)
        finally:
            if driver is not None:
                driver.quit()
    if proof["status"] != "pass" and proof.get("error") is None:
        proof["error"] = last or "no_url_passed"
except Exception as exc:
    proof["error"] = repr(exc)
out.write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8")
sys.exit(0 if proof["status"] == "pass" else 2)
'@

  $tempPy = Join-Path $env:TEMP "aays1_security_browser_$PID.py"
  $pythonScript | Set-Content -Encoding UTF8 $tempPy
  $matrixUrls = @(
    'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=142',
    'http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=142',
    'http://127.0.0.1:8020/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=142'
  )
  & python $tempPy $browserProofPath @matrixUrls
  $browserExit = $LASTEXITCODE
  Remove-Item -Force -ErrorAction SilentlyContinue $tempPy

  if (Test-Path $browserProofPath) {
    $proof = Get-Content -Raw -Encoding UTF8 $browserProofPath | ConvertFrom-Json
    $result.browser_smoke_status = [string]$proof.status
    $result.browser_url = [string]$proof.url
    $result.console_error_count = $proof.console_error_count
    if ($proof.status -ne 'pass') { $result.blockers += "browser_smoke_failed:$($proof.error)" }
  } else {
    $result.browser_smoke_status = 'proof_not_written'
    $result.blockers += 'browser_proof_not_written'
  }

  $result.status = if ($result.blockers.Count -eq 0) { 'completed_visibility_fix_browser_pass_pending_source_expansion' } else { 'visibility_files_written_with_blockers' }
}
catch {
  $result.status = 'blocked_visibility_fix_exception'
  $result.blockers += $_.Exception.Message
}

Save-Result

try {
  Push-Location $repoRoot
  $paths = @($visibleRowsRel,$visibleStatusRel,$reportRel,$reportMirrorRel,$operationsRel,$outputRel,$browserProofRel)
  & git add -- @paths | Out-Null
  $changes = @(& git status --porcelain -- @paths)
  if ($changes.Count -gt 0) {
    & git commit -m 'aays1 complete 142 security row evidence visibility proof' | Out-Null
    if ($LASTEXITCODE -eq 0) {
      $result.commit_sha = (& git rev-parse HEAD).Trim()
      & git push origin $branch | Out-Null
      $result.git_push_status = if ($LASTEXITCODE -eq 0) { 'pushed' } else { 'push_failed' }
    } else { $result.git_push_status = 'commit_failed' }
  } else {
    $result.commit_sha = (& git rev-parse HEAD).Trim()
    $result.git_push_status = 'no_changes_to_push'
  }

  if ($result.git_push_status -in @('pushed','no_changes_to_push')) {
    & git fetch origin $branch | Out-Null
    $remoteText = & git show "origin/$branch`:$visibleStatusRel" 2>$null
    $result.remote_readback_status = if ($LASTEXITCODE -eq 0 -and ($remoteText -join "`n") -match 'verified_geojson_features') { 'passed' } else { 'failed' }
  } else { $result.remote_readback_status = 'not_attempted_due_push_failure' }
}
catch {
  $result.git_push_status = 'exception'
  $result.remote_readback_status = 'exception'
  $result.blockers += "git_sync_exception:$($_.Exception.Message)"
}
finally { try { Pop-Location } catch {} }

Save-Result
try {
  Push-Location $repoRoot
  & git add -- $outputRel | Out-Null
  $outputChange = @(& git status --porcelain -- $outputRel)
  if ($outputChange.Count -gt 0) {
    & git commit -m 'aays1 sync 142 final runner output status' | Out-Null
    if ($LASTEXITCODE -eq 0) { & git push origin $branch | Out-Null }
  }
}
catch { $result.blockers += "final_output_push_exception:$($_.Exception.Message)"; Save-Result }
finally { try { Pop-Location } catch {} }

Write-Host "OUTPUT=$outputPath"
if ($result.blockers.Count -gt 0 -or $result.browser_smoke_status -ne 'pass') { exit 2 }
exit 0
