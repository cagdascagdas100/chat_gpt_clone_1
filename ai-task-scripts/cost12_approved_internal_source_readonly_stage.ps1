$ErrorActionPreference = "Continue"
Set-StrictMode -Version Latest

$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$OutDir = Join-Path $BridgeRoot "ai-results"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$TaskId = "cost12-approved-internal-source-readonly-stage-20260525"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Report = Join-Path $OutDir "cost12_approved_internal_source_readonly_stage_$Stamp.md"
$Result = Join-Path $OutDir "cost12_approved_internal_source_readonly_stage.result.json"
$StageCsv = Join-Path $OutDir "cost12_approved_internal_source_ratecard_stage_$Stamp.csv"
$ApiLog = Join-Path $OutDir "cost12_approved_internal_source_preview_$Stamp.log"

$CandidateCsv = Join-Path $ProjectRoot "docs\chatgpt_handoff\cost12_internal_approval_source_path\cost12_approved_internal_source_with_limitations_candidate.csv"
$RateCard = Join-Path $ProjectRoot "tools\cost_uk_real_engine\config\building_type_rate_card_uk.csv"

function Add-ReportLine([string]$line) {
  $line | Add-Content -Encoding UTF8 $Report
}

"# COST12 Approved Internal Source Read-only Stage" | Set-Content -Encoding UTF8 $Report
Add-ReportLine "time=$Stamp"
Add-ReportLine "task_id=$TaskId"
Add-ReportLine "db_write=false"
Add-ReportLine "production_deploy=false"
Add-ReportLine "fake_data=false"
Add-ReportLine ""

$decision = "UNKNOWN"
$validationErrors = New-Object System.Collections.Generic.List[string]
$apiPass = $false
$stageCreated = $false
$candidate = $null

try {
  if (-not (Test-Path $CandidateCsv)) {
    $validationErrors.Add("missing_candidate_csv:$CandidateCsv")
  } else {
    $rows = Import-Csv $CandidateCsv
    if (@($rows).Count -lt 1) { $validationErrors.Add("candidate_csv_empty") }
    else { $candidate = $rows[0] }
  }

  if ($candidate -ne $null) {
    $required = @(
      "scenario_version", "building_type", "spec_grade", "region",
      "base_rate_gbp_per_gia_m2", "source_type", "source_reliability",
      "production_ready_candidate", "final_ready_confirmed", "db_write", "production_deploy", "fake_data"
    )
    foreach ($f in $required) {
      if (-not ($candidate.PSObject.Properties.Name -contains $f)) { $validationErrors.Add("missing_field:$f") }
    }

    if ($candidate.scenario_version -ne "cost_uk_v1") { $validationErrors.Add("scenario_version_not_cost_uk_v1") }
    if ($candidate.building_type -ne "retail") { $validationErrors.Add("building_type_not_retail") }
    if ($candidate.spec_grade -ne "mid") { $validationErrors.Add("spec_grade_not_mid") }
    if ($candidate.region -ne "UK") { $validationErrors.Add("region_not_UK") }
    if ($candidate.source_type -ne "approved_internal_source_with_limitations") { $validationErrors.Add("source_type_not_approved_internal_source_with_limitations") }
    if ([string]$candidate.production_ready_candidate -ne "true") { $validationErrors.Add("production_ready_candidate_not_true") }
    if ([string]$candidate.final_ready_confirmed -ne "false") { $validationErrors.Add("final_ready_confirmed_must_remain_false") }
    if ([string]$candidate.db_write -ne "false") { $validationErrors.Add("db_write_not_false") }
    if ([string]$candidate.production_deploy -ne "false") { $validationErrors.Add("production_deploy_not_false") }
    if ([string]$candidate.fake_data -ne "false") { $validationErrors.Add("fake_data_not_false") }
  }

  Add-ReportLine "## Candidate validation"
  if ($validationErrors.Count -eq 0) {
    Add-ReportLine "PASS: candidate metadata valid for approved-internal-source-with-limitations read-only staging."
  } else {
    Add-ReportLine "FAIL: validation errors:"
    foreach ($e in $validationErrors) { Add-ReportLine "- $e" }
  }

  Add-ReportLine ""
  Add-ReportLine "## Stage output"

  if ($validationErrors.Count -eq 0) {
    $candidate | Export-Csv -NoTypeInformation -Encoding UTF8 $StageCsv
    $stageCreated = $true
    Add-ReportLine "stage_csv=$StageCsv"
  }

  Add-ReportLine ""
  Add-ReportLine "## Existing rate-card status"
  if (Test-Path $RateCard) {
    $rateRows = Import-Csv $RateCard
    $retailRows = @($rateRows | Where-Object { $_.building_type -eq "retail" })
    Add-ReportLine "rate_card_exists=true"
    Add-ReportLine "rate_card_rows=$(@($rateRows).Count)"
    Add-ReportLine "rate_card_retail_rows=$(@($retailRows).Count)"
  } else {
    Add-ReportLine "rate_card_exists=false"
  }

  Add-ReportLine ""
  Add-ReportLine "## API preview read-only smoke"

  $body = @{
    parcel_id = 1
    building_type = "retail"
    building_subtype = "restaurant"
    quality_level = "mid"
    gross_internal_area_m2 = 250
    sales_area_m2 = 200
    fit_out_level = "mid"
    cooling_kitchen_need = $true
    db_write = $false
    production_deploy = $false
  } | ConvertTo-Json -Depth 10

  try {
    $resp = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8010/cost/estimate/preview" -ContentType "application/json" -Body $body -TimeoutSec 20
    $apiPass = $true
    ($resp | ConvertTo-Json -Depth 20) | Set-Content -Encoding UTF8 $ApiLog
    Add-ReportLine "PASS: POST /cost/estimate/preview"
  } catch {
    $apiPass = $false
    $err = $_.Exception.Message
    $bodyText = ""
    try {
      $stream = $_.Exception.Response.GetResponseStream()
      if ($stream) {
        $reader = New-Object System.IO.StreamReader($stream)
        $bodyText = $reader.ReadToEnd()
      }
    } catch {}
    "ERROR: $err`n$bodyText" | Set-Content -Encoding UTF8 $ApiLog
    Add-ReportLine "FAIL: POST /cost/estimate/preview"
    Add-ReportLine "api_log=$ApiLog"
  }

  if ($validationErrors.Count -eq 0 -and $stageCreated -and $apiPass) {
    $decision = "APPROVED_INTERNAL_SOURCE_STAGE_AND_PREVIEW_PASS"
  } elseif ($validationErrors.Count -eq 0 -and $stageCreated -and -not $apiPass) {
    $decision = "APPROVED_INTERNAL_SOURCE_STAGE_READY_PREVIEW_STILL_BLOCKED_BY_SERVICE_IMPORT"
  } else {
    $decision = "APPROVED_INTERNAL_SOURCE_STAGE_FAILED_VALIDATION"
  }

} catch {
  $decision = "SCRIPT_ERROR"
  $validationErrors.Add($_.Exception.Message)
  Add-ReportLine "SCRIPT_ERROR: $($_.Exception.Message)"
}

Add-ReportLine ""
Add-ReportLine "## Decision"
Add-ReportLine $decision

$out = [ordered]@{
  task_id = $TaskId
  decision = $decision
  report = $Report
  stage_csv = $StageCsv
  api_log = $ApiLog
  candidate_csv = $CandidateCsv
  validation_errors = @($validationErrors)
  stage_created = $stageCreated
  api_preview_pass = $apiPass
  db_write = $false
  production_deploy = $false
  fake_data = $false
  final_ready_confirmed = $false
}

$out | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $Result
Get-Content $Report -Raw
