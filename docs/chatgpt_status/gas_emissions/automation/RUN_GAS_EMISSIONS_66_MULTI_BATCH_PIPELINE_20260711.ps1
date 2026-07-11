[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'

function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Json([string]$Path,[object]$Value) { Ensure-Dir (Split-Path -Parent $Path); [IO.File]::WriteAllText($Path,(($Value | ConvertTo-Json -Depth 80)+"`n"),[Text.UTF8Encoding]::new($false)) }
function Set-Prop([object]$Object,[string]$Name,[object]$Value) { $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force }
function Row-Count([string]$Path) { $o=Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json; return @($o.rows).Count }
function Parse-Number([object]$Value) { return [double]::Parse([string]$Value,[Globalization.CultureInfo]::InvariantCulture) }

$repoRoot=[IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$taskId=[string]$env:AAYS_TASK_ID
$pageKey=[string]$env:AAYS_PAGE_KEY
$branch=[string]$env:AAYS_TARGET_BRANCH
if (-not $repoRoot -or -not $taskId -or $pageKey -ne 'gas_emissions') { throw 'GAS_EMISSIONS_66_MUST_RUN_INSIDE_CANONICAL_SHARED_RUNNER' }
if ($branch -ne 'codex/aays-single-runner-v5-20260706') { throw 'GAS_EMISSIONS_66_WRONG_BRANCH' }

$rowsRel='england_map_web\data\program_layer_matrix\gas_emissions_visible_rows_latest.json'
$statusRel='england_map_web\data\program_layer_matrix\gas_emissions_status_latest.json'
$matrixRel='england_map_web\TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$rowsPath=Join-Path $repoRoot $rowsRel
$statusPath=Join-Path $repoRoot $statusRel
$matrixPath=Join-Path $repoRoot $matrixRel
$pipeline37=Join-Path $repoRoot 'docs\chatgpt_status\gas_emissions\automation\RUN_GAS_EMISSIONS_37_MULTI_STAGE_PIPELINE_20260711_FIX.ps1'

$currentCount=Row-Count $rowsPath
if ($currentCount -eq 28) {
  if (-not (Test-Path -LiteralPath $pipeline37)) { throw 'MISSING_37_PIPELINE' }
  & powershell -NoProfile -ExecutionPolicy Bypass -File $pipeline37
  if ($LASTEXITCODE -ne 0) { throw 'PREREQUISITE_37_PIPELINE_FAILED' }
  $currentCount=Row-Count $rowsPath
}
if ($currentCount -ne 37 -and $currentCount -ne 66) { throw "EXPECTED_37_OR_66_ROWS_AFTER_PREREQUISITE: $currentCount" }

$sourceUrl='https://assets.publishing.service.gov.uk/media/68653c7ee6c3cc924228943f/2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv'
$sourceDir='F:\TerraYield_AAYS_Portable\sources\gas_emissions'
$sourceLocalPath=Join-Path $sourceDir '2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv'
Ensure-Dir $sourceDir
if (-not (Test-Path -LiteralPath $sourceLocalPath) -or (Get-Item -LiteralPath $sourceLocalPath).Length -lt 1000000) {
  $tmp=$sourceLocalPath+'.download_'+[Guid]::NewGuid().ToString('N')
  Invoke-WebRequest -UseBasicParsing -Uri $sourceUrl -OutFile $tmp -TimeoutSec 600
  if ((Get-Item -LiteralPath $tmp).Length -lt 1000000) { throw 'OFFICIAL_SOURCE_DOWNLOAD_TOO_SMALL' }
  Move-Item -LiteralPath $tmp -Destination $sourceLocalPath -Force
}
$sourceSha256=(Get-FileHash -LiteralPath $sourceLocalPath -Algorithm SHA256).Hash.ToLowerInvariant()
$headLines=@([IO.File]::ReadLines($sourceLocalPath) | Select-Object -First 260)
$csvRows=@($headLines | ConvertFrom-Csv)

$manifestRels=@(
 'docs\chatgpt_status\gas_emissions\candidates\152_gas_emissions_official_industry_2005_candidates_20260711.json',
 'docs\chatgpt_status\gas_emissions\candidates\153_gas_emissions_official_public_sector_2005_candidates_20260711.json',
 'docs\chatgpt_status\gas_emissions\candidates\154_gas_emissions_official_domestic_2005_candidates_20260711.json'
)
$verified=New-Object System.Collections.Generic.List[object]
foreach ($manifestRel in $manifestRels) {
  $manifestPath=Join-Path $repoRoot $manifestRel
  $manifest=Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
  foreach ($candidate in @($manifest.candidates)) {
    $matches=@($csvRows | Where-Object {
      [string]$_.'Local Authority Code' -eq 'E06000001' -and
      [int]$_.'Calendar Year' -eq 2005 -and
      [string]$_.'LA GHG Sector' -eq [string]$candidate.sector -and
      [string]$_.'LA GHG Sub-sector' -eq [string]$candidate.sub_sector -and
      [string]$_.'Greenhouse gas' -eq [string]$candidate.greenhouse_gas
    })
    if ($matches.Count -ne 1) { throw "OFFICIAL_CSV_MATCH_COUNT_NOT_ONE: $($candidate.row_id) count=$($matches.Count)" }
    $m=$matches[0]
    $actualTerritorial=Parse-Number $m.'Territorial emissions (kt CO2e)'
    $actualScope=Parse-Number $m.'Emissions within the scope of influence of LAs (kt CO2)'
    if ([Math]::Abs($actualTerritorial-[double]$candidate.territorial_emissions_kt_co2e) -gt 0.000000001) { throw "TERRITORIAL_VALUE_MISMATCH: $($candidate.row_id)" }
    if ([Math]::Abs($actualScope-[double]$candidate.scope_of_influence_kt_co2) -gt 0.000000001) { throw "SCOPE_VALUE_MISMATCH: $($candidate.row_id)" }
    $verified.Add([pscustomobject][ordered]@{
      row_id=[string]$candidate.row_id; calendar_year=2005; sector=[string]$candidate.sector; sub_sector=[string]$candidate.sub_sector; greenhouse_gas=[string]$candidate.greenhouse_gas
      territorial_emissions_kt_co2e=$actualTerritorial; scope_of_influence_kt_co2=$actualScope; source_lines=[string]$candidate.source_preview_line
      matching_method='official_govuk_preview_plus_downloaded_csv_exact_fields'; calculation_explanation="Official GOV.UK preview $($candidate.source_preview_line) and downloaded CSV exact-key/value match; no parcel allocation or derived calculation applied."
      confidence_percent=94; accuracy_score_4='3.4/4'; needs_manual_review=$true; parcel_binding_status='PENDING'
      source_url='https://www.gov.uk/csv-preview/68653c7ee6c3cc924228943f/2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv'; source_download_url=$sourceUrl
      source_local_raw_path=$sourceLocalPath; source_local_sha256=$sourceSha256; source_manifest_path=($manifestRel -replace '\\','/')
      visible_rows_artifact_path='england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'; status_path='england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
      report_path='docs/chatgpt_status/gas_emissions/reports/156_gas_emissions_66_multi_batch_pipeline_20260711.json'; changed_in_latest_run=$true; is_new_in_latest_batch=$true
      display_badge='KAYNAKLI_YENI'; served_commit_sha='PENDING_RUNNER_COMMIT'; artifact_sha='SEE_STATUS_ARTIFACT_SHA256'
    })
  }
}
if ($verified.Count -ne 29) { throw "VERIFIED_COUNT_NOT_29: $($verified.Count)" }

$visible=Get-Content -LiteralPath $rowsPath -Raw -Encoding UTF8 | ConvertFrom-Json
$existing=@($visible.rows)
$targetIds=@($verified | ForEach-Object { [string]$_.row_id })
$oldRows=@($existing | Where-Object { $targetIds -notcontains [string]$_.row_id })
foreach ($row in $oldRows) { Set-Prop $row 'changed_in_latest_run' $false; Set-Prop $row 'is_new_in_latest_batch' $false; Set-Prop $row 'display_badge' 'KAYNAKLI_MEVCUT'; Set-Prop $row 'source_local_raw_path' $sourceLocalPath; Set-Prop $row 'source_local_sha256' $sourceSha256 }
$visible.rows=@($oldRows)+@($verified)
if (@($visible.rows).Count -ne 66) { throw "TARGET_VISIBLE_COUNT_NOT_66: $(@($visible.rows).Count)" }
Set-Prop $visible 'status' 'OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_66'
Set-Prop $visible 'previous_visible_row_count' 37
Set-Prop $visible 'previous_visible_rows_count' 37
Set-Prop $visible 'new_rows_added_this_run' 29
Set-Prop $visible 'new_rows_in_latest_batch' 29
Set-Prop $visible 'visible_row_count' 66
Set-Prop $visible 'visible_rows_count' 66
Set-Prop $visible 'latest_batch_id' 'gas_emissions_official_industry_public_domestic_2005_20260711_01'
Set-Prop $visible 'source_row_accuracy_score_4' '3.4/4'
Set-Prop $visible 'accuracy_note' '66 official GOV.UK rows; latest 29 passed preview-line and downloaded-CSV exact-field/value checks. Parcel binding remains pending.'
Set-Prop $visible 'source_local_raw_path' $sourceLocalPath
Set-Prop $visible 'source_local_sha256' $sourceSha256
Set-Prop $visible 'methodology_evidence_path' 'docs/chatgpt_status/gas_emissions/evidence/155_gas_emissions_official_source_scope_and_methodology_20260711.json'
Set-Prop $visible 'browser_smoke_passed_for_66_rows' $false
Set-Prop $visible 'updated_at' ((Get-Date).ToUniversalTime().ToString('o'))
Set-Prop $visible 'final_ready' $false
Write-Json $rowsPath $visible
$artifactSha256=(Get-FileHash -LiteralPath $rowsPath -Algorithm SHA256).Hash.ToLowerInvariant()

$status=Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
Set-Prop $status 'status' 'OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_66'
Set-Prop $status 'previous_visible_row_count' 37
Set-Prop $status 'new_rows_added_this_run' 29
Set-Prop $status 'visible_rows_count' 66
Set-Prop $status 'current_visible_change_rows' 29
Set-Prop $status 'verification_score_after' '3.4/4'
Set-Prop $status 'source_local_raw_path' $sourceLocalPath
Set-Prop $status 'source_local_sha256' $sourceSha256
Set-Prop $status 'artifact_sha256' $artifactSha256
Set-Prop $status 'methodology_evidence_path' 'docs/chatgpt_status/gas_emissions/evidence/155_gas_emissions_official_source_scope_and_methodology_20260711.json'
Set-Prop $status 'browser_smoke_passed' $false
Set-Prop $status 'parcel_binding_gate_passed' $false
Set-Prop $status 'final_ready' $false
Set-Prop $status 'fake_data' $false
Write-Json $statusPath $status

$servedRoot='F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
foreach ($rel in @($rowsRel,$statusRel,$matrixRel)) { $src=Join-Path $repoRoot $rel; $dst=Join-Path $servedRoot $rel; Ensure-Dir (Split-Path -Parent $dst); Copy-Item -LiteralPath $src -Destination $dst -Force }
$httpRowsUrl='http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json?gas66='+[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$httpCount=-1
for ($i=0;$i -lt 15;$i++) { try { $r=Invoke-RestMethod -Uri $httpRowsUrl -TimeoutSec 20 -Headers @{'Cache-Control'='no-cache'}; $httpCount=@($r.rows).Count; if ($httpCount -eq 66) { break } } catch {}; Start-Sleep -Seconds 2 }
if ($httpCount -ne 66) { throw "HTTP_8012_ROW_COUNT_NOT_66: $httpCount" }

$tmpBase=Join-Path ([IO.Path]::GetTempPath()) $taskId
$tmpPy=$tmpBase+'.py'; $tmpExpected=$tmpBase+'.expected.json'; $tmpOut=$tmpBase+'.result.json'
Write-Json $tmpExpected @($targetIds)
$py=@'
import json,re,sys,time
from pathlib import Path
out=Path(sys.argv[1]); expected=set(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")))
url="http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=gas66&ts="+str(int(time.time()))
result={"status":"FAIL","url":url,"unique_row_count":0,"new_marker_count":0,"manual_marker_on_new_count":0,"headers":[],"console_errors":[],"error":None}
driver=None
try:
 from selenium import webdriver
 from selenium.webdriver.common.by import By
 from selenium.webdriver.support.ui import WebDriverWait,Select
 options=webdriver.ChromeOptions(); options.add_argument("--headless=new"); options.add_argument("--disable-gpu"); options.add_argument("--no-sandbox"); options.add_argument("--disable-dev-shm-usage"); options.add_argument("--window-size=1920,1400"); options.set_capability("goog:loggingPrefs",{"browser":"ALL"})
 driver=webdriver.Chrome(options=options); driver.get(url); wait=WebDriverWait(driver,60); wait.until(lambda d:d.find_element(By.ID,"layerSelect")); Select(driver.find_element(By.ID,"layerSelect")).select_by_value("gas"); wait.until(lambda d:"66 satır" in d.find_element(By.ID,"pageInfo").text)
 rows={}
 for _ in range(10):
  for tr in driver.find_elements(By.CSS_SELECTOR,"#table tbody tr"):
   cells=tr.find_elements(By.TAG_NAME,"td")
   if len(cells)>1 and cells[1].text.strip(): rows[cells[1].text.strip()]=cells[0].text.strip()
  info=driver.find_element(By.ID,"pageInfo").text
  m=re.search(r"Sayfa\s+(\d+)\s*/\s*(\d+)",info)
  if not m or int(m.group(1))>=int(m.group(2)): break
  driver.find_element(By.ID,"next").click(); wait.until(lambda d:re.search(r"Sayfa\s+%d\s*/"%(int(m.group(1))+1),d.find_element(By.ID,"pageInfo").text))
 headers=[x.text.strip() for x in driver.find_elements(By.CSS_SELECTOR,"#table thead th")]
 required_headers={"Hesap açıklaması","Parcel binding","Ham yerel kaynak","Visible artifact","Status yolu","Rapor yolu","Served commit","Artifact SHA"}
 severe=[]
 try: severe=[e for e in driver.get_log("browser") if str(e.get("level","")).upper()=="SEVERE"]
 except Exception: pass
 new_count=sum(1 for rid in expected if "YENİ / LATEST" in rows.get(rid,"")); manual_count=sum(1 for rid in expected if "MANUEL İNCELEME" in rows.get(rid,""))
 passed=len(rows)==66 and expected.issubset(rows) and new_count==29 and manual_count==29 and required_headers.issubset(set(headers)) and not severe
 result.update({"status":"PASS" if passed else "FAIL","unique_row_count":len(rows),"new_marker_count":new_count,"manual_marker_on_new_count":manual_count,"expected_new_rows_present":expected.issubset(rows),"headers":headers,"required_headers_present":required_headers.issubset(set(headers)),"page_info":driver.find_element(By.ID,"pageInfo").text,"console_errors":severe,"title":driver.title})
 if not passed: result["error"]="count_ids_markers_headers_or_console_check_failed"
except Exception as exc: result["error"]=f"{type(exc).__name__}: {exc}"
finally:
 if driver:
  try: driver.quit()
  except Exception: pass
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
sys.exit(0 if result["status"]=="PASS" else 1)
'@
[IO.File]::WriteAllText($tmpPy,$py,[Text.UTF8Encoding]::new($false))
$python=Get-Command python -ErrorAction SilentlyContinue
if ($python) { & $python.Source $tmpPy $tmpOut $tmpExpected } else { $p=Get-Command py -ErrorAction Stop; & $p.Source -3 $tmpPy $tmpOut $tmpExpected }
$browserExit=$LASTEXITCODE
$result=Get-Content -LiteralPath $tmpOut -Raw -Encoding UTF8 | ConvertFrom-Json
$browserPassed=($browserExit -eq 0 -and [string]$result.status -eq 'PASS' -and [int]$result.unique_row_count -eq 66)

$geoPath=Join-Path $repoRoot 'england_map_web\data\parcel_emissions_scores.geojson'
$geoAudit=[ordered]@{path='england_map_web/data/parcel_emissions_scores.geojson';exists=(Test-Path -LiteralPath $geoPath);feature_count=0;complete_required_field_count=0;required_fields=@('emission_percent','level','risk_color','confidence','source','source_date','matching_method','calculation_explanation')}
if ($geoAudit.exists) { $g=Get-Content -LiteralPath $geoPath -Raw -Encoding UTF8 | ConvertFrom-Json; $features=@($g.features); $geoAudit.feature_count=$features.Count; foreach($f in $features){$p=$f.properties; $ok=$true; foreach($name in $geoAudit.required_fields){if($null -eq $p.$name -or [string]$p.$name -eq ''){$ok=$false;break}}; if($ok){$geoAudit.complete_required_field_count++}} }
$appPath=Join-Path $repoRoot 'england_map_web\app.js'; $appText=if(Test-Path -LiteralPath $appPath){Get-Content -LiteralPath $appPath -Raw -Encoding UTF8}else{''}
$uiAudit=[ordered]@{air_icon=($appText -match 'air\.png'); emission_percent=($appText -match 'emission_percent'); level=($appText -match '\blevel\b'); risk_color=($appText -match 'risk_color'); confidence=($appText -match 'confidence'); source_date=($appText -match 'source_date'); matching_method=($appText -match 'matching_method'); calculation_explanation=($appText -match 'calculation_explanation'); legend_reference=($appText -match 'legend')}

$reportRel='docs/chatgpt_status/gas_emissions/reports/156_gas_emissions_66_multi_batch_pipeline_20260711.json'
$reportPath=Join-Path $repoRoot ($reportRel -replace '/','\')
$resultStatusRel='docs/chatgpt_status/gas_emissions/status/156_gas_emissions_66_multi_batch_pipeline_latest.json'
$resultStatusPath=Join-Path $repoRoot ($resultStatusRel -replace '/','\')
$payload=[ordered]@{
 task_id=$taskId; page_key=$pageKey; target_branch=$branch; status=if($browserPassed){'PASS_66_VISIBLE_SOURCE_ROWS'}else{'FAIL_BROWSER_66'}; generated_by_runner=$true; generated_at=(Get-Date).ToUniversalTime().ToString('o')
 previous_visible_rows=37; new_verified_rows=29; visible_rows=66; candidate_batches=@('Industry 2005: 11','Public Sector 2005: 9','Domestic 2005: 9'); confidence_percent=94; accuracy_score_4='3.4/4'
 source_url=$sourceUrl; source_local_raw_path=$sourceLocalPath; source_local_sha256=$sourceSha256; artifact_sha256=$artifactSha256; served_http_row_count=$httpCount
 browser=$result; browser_smoke_passed=$browserPassed; geojson_audit=$geoAudit; ui_reference_audit=$uiAudit
 parcel_binding_gate_passed=$false; blocker=if($geoAudit.complete_required_field_count -lt $geoAudit.feature_count -or ($uiAudit.Values -contains $false)){'PARCEL_GEOJSON_OR_UI_REQUIRED_FIELDS_INCOMPLETE'}else{'PARCEL_BINDING_EVIDENCE_STILL_REQUIRED'}
 report_path=$reportRel; single_runner_only=$true; new_runner=$false; parallel_runner=$false; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; git_push_status='pending_runner_wrapper'
}
Write-Json $reportPath $payload; Write-Json $resultStatusPath $payload
if ($browserPassed) { $status=Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json; Set-Prop $status 'browser_smoke_passed' $true; Set-Prop $status 'browser_smoke_row_count' 66; Set-Prop $status 'browser_smoke_new_marker_count' 29; Set-Prop $status 'browser_smoke_report_path' $reportRel; Set-Prop $status 'browser_smoke_passed_at' ((Get-Date).ToUniversalTime().ToString('o')); Set-Prop $status 'next_required_runner_action' 'Resolve parcel-level binding and missing GeoJSON/UI evidence without inventing allocation; keep final_ready false.'; Set-Prop $status 'final_ready' $false; Write-Json $statusPath $status }
Remove-Item -LiteralPath $tmpPy,$tmpExpected,$tmpOut -Force -ErrorAction SilentlyContinue
if (-not $browserPassed) { throw 'GAS_EMISSIONS_66_BROWSER_SMOKE_FAILED' }
Write-Output ($payload | ConvertTo-Json -Depth 80)
