$ErrorActionPreference = "Continue"
Set-StrictMode -Version Latest

$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$OutDir = Join-Path $BridgeRoot "ai-results"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$TaskId = "cost12-apply-approved-internal-source-ratecard-readonly-20260525"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Report = Join-Path $OutDir "cost12_apply_approved_internal_source_ratecard_readonly_$Stamp.md"
$Result = Join-Path $OutDir "cost12_apply_approved_internal_source_ratecard_readonly.result.json"
$ApiLog = Join-Path $OutDir "cost12_apply_approved_internal_source_preview_$Stamp.log"

$CandidateCsv = Join-Path $ProjectRoot "docs\chatgpt_handoff\cost12_internal_approval_source_path\cost12_approved_internal_source_with_limitations_candidate.csv"
$RateCard = Join-Path $ProjectRoot "tools\cost_uk_real_engine\config\building_type_rate_card_uk.csv"
$Backup = Join-Path $OutDir "building_type_rate_card_uk.before_cost12_approved_internal_source_$Stamp.csv"

function Add-ReportLine([string]$line) { $line | Add-Content -Encoding UTF8 $Report }
function Set-IfField($obj, [string]$field, $value) {
  if ($obj.PSObject.Properties.Name -contains $field) { $obj.$field = $value }
}

"# COST12 Apply Approved Internal Source To Ratecard Read-only" | Set-Content -Encoding UTF8 $Report
Add-ReportLine "time=$Stamp"
Add-ReportLine "task_id=$TaskId"
Add-ReportLine "db_write=false"
Add-ReportLine "production_deploy=false"
Add-ReportLine "fake_data=false"
Add-ReportLine "local_config_backup=true"
Add-ReportLine "final_ready_confirmed=false"
Add-ReportLine ""

$decision = "UNKNOWN"
$errors = New-Object System.Collections.Generic.List[string]
$applied = $false
$previewPass = $false
$existingMatchCount = 0
$rowCountBefore = 0
$rowCountAfter = 0

try {
  if (-not (Test-Path $CandidateCsv)) { $errors.Add("missing_candidate_csv:$CandidateCsv") }
  if (-not (Test-Path $RateCard)) { $errors.Add("missing_ratecard:$RateCard") }

  if ($errors.Count -eq 0) {
    $candidateRows = Import-Csv $CandidateCsv
    if (@($candidateRows).Count -lt 1) { $errors.Add("candidate_csv_empty") }
    $candidate = $candidateRows[0]

    if ($candidate.scenario_version -ne "cost_uk_v1") { $errors.Add("candidate_scenario_not_cost_uk_v1") }
    if ($candidate.building_type -ne "retail") { $errors.Add("candidate_building_type_not_retail") }
    if ($candidate.spec_grade -ne "mid") { $errors.Add("candidate_spec_grade_not_mid") }
    if ($candidate.region -ne "UK") { $errors.Add("candidate_region_not_UK") }
    if ($candidate.source_type -ne "approved_internal_source_with_limitations") { $errors.Add("candidate_source_type_invalid") }
    if ([string]$candidate.production_ready_candidate -ne "true") { $errors.Add("candidate_production_ready_candidate_not_true") }
    if ([string]$candidate.final_ready_confirmed -ne "false") { $errors.Add("candidate_final_ready_confirmed_must_be_false") }
    if ([string]$candidate.db_write -ne "false") { $errors.Add("candidate_db_write_not_false") }
    if ([string]$candidate.production_deploy -ne "false") { $errors.Add("candidate_production_deploy_not_false") }
    if ([string]$candidate.fake_data -ne "false") { $errors.Add("candidate_fake_data_not_false") }
  }

  if ($errors.Count -eq 0) {
    Copy-Item -LiteralPath $RateCard -Destination $Backup -Force
    $rateRows = @(Import-Csv $RateCard)
    $rowCountBefore = $rateRows.Count

    $existing = @($rateRows | Where-Object {
      ($_.building_type -eq "retail") -and
      ($_.spec_grade -eq "mid" -or $_.quality_level -eq "mid" -or $_.grade -eq "mid") -and
      ($_.region -eq "UK") -and
      ($_.scenario_version -eq "cost_uk_v1" -or $_.scenario -eq "cost_uk_v1")
    })
    $existingMatchCount = $existing.Count

    Add-ReportLine "## Ratecard before"
    Add-ReportLine "ratecard=$RateCard"
    Add-ReportLine "backup=$Backup"
    Add-ReportLine "row_count_before=$rowCountBefore"
    Add-ReportLine "existing_retail_mid_uk_cost_uk_v1_rows=$existingMatchCount"
    Add-ReportLine ""

    if ($existingMatchCount -eq 0) {
      $headers = @()
      if ($rateRows.Count -gt 0) { $headers = @($rateRows[0].PSObject.Properties.Name) }
      else { $errors.Add("ratecard_has_no_headers_or_rows") }

      if ($errors.Count -eq 0) {
        $newRow = [ordered]@{}
        foreach ($h in $headers) { $newRow[$h] = "" }
        $newObj = New-Object psobject -Property $newRow

        Set-IfField $newObj "scenario_version" "cost_uk_v1"
        Set-IfField $newObj "scenario" "cost_uk_v1"
        Set-IfField $newObj "building_type" "retail"
        Set-IfField $newObj "spec_grade" "mid"
        Set-IfField $newObj "quality_level" "mid"
        Set-IfField $newObj "grade" "mid"
        Set-IfField $newObj "region" "UK"
        Set-IfField $newObj "base_rate_gbp_per_gia_m2" "1200"
        Set-IfField $newObj "base_rate" "1200"
        Set-IfField $newObj "rate" "1200"
        Set-IfField $newObj "base_rate_range_gbp_per_gia_m2" "400-3500"
        Set-IfField $newObj "base_month" "INTERNAL_APPROVAL_2026-05"
        Set-IfField $newObj "source_id" "approved_internal_retail_fitout_seed_catalog_20260525"
        Set-IfField $newObj "source_url_or_path" "tools/cost_uk_real_engine/config/cost_item_catalog_12cost.csv"
        Set-IfField $newObj "source_url" "tools/cost_uk_real_engine/config/cost_item_catalog_12cost.csv"
        Set-IfField $newObj "source_type" "approved_internal_source_with_limitations"
        Set-IfField $newObj "source_reliability" "0.60"
        Set-IfField $newObj "confidence_band" "MEDIUM_WITH_LIMITATIONS"
        Set-IfField $newObj "production_ready" "false"
        Set-IfField $newObj "production_ready_candidate" "true"
        Set-IfField $newObj "final_ready_confirmed" "false"
        Set-IfField $newObj "review_mode" "false"
        Set-IfField $newObj "db_write" "false"
        Set-IfField $newObj "production_deploy" "false"
        Set-IfField $newObj "fake_data" "false"
        Set-IfField $newObj "notes" "Approved internal source with limitations. Retail fit-out/shopfront benchmark only; not full shell construction; replace when verified external source is obtained."
        Set-IfField $newObj "applicability_note" "Retail fit-out / shopfront signage benchmark only; not full shell construction. Restaurant/supermarket scope may require adjustment."

        $updatedRows = @($rateRows + $newObj)
        $updatedRows | Export-Csv -NoTypeInformation -Encoding UTF8 $RateCard
        $applied = $true
      }
    } else {
      Add-ReportLine "existing row already present; no append applied."
      $applied = $false
    }

    $afterRows = @(Import-Csv $RateCard)
    $rowCountAfter = $afterRows.Count
    Add-ReportLine "## Ratecard after"
    Add-ReportLine "row_count_after=$rowCountAfter"
    Add-ReportLine "applied=$applied"
  }

  Add-ReportLine ""
  Add-ReportLine "## Preview smoke"
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
    $previewPass = $true
    ($resp | ConvertTo-Json -Depth 20) | Set-Content -Encoding UTF8 $ApiLog
    Add-ReportLine "PASS: POST /cost/estimate/preview"
  } catch {
    $previewPass = $false
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
    Add-ReportLine "note=If API was already running, restart may be required for CSV/config reload."
  }

  if ($errors.Count -gt 0) {
    $decision = "APPLY_APPROVED_INTERNAL_SOURCE_FAILED_VALIDATION"
  } elseif ($previewPass) {
    $decision = "APPROVED_INTERNAL_SOURCE_APPLIED_AND_PREVIEW_PASS"
  } elseif ($applied -or $existingMatchCount -gt 0) {
    $decision = "APPROVED_INTERNAL_SOURCE_APPLIED_PREVIEW_REQUIRES_API_RESTART_OR_IMPORT_RELOAD"
  } else {
    $decision = "APPROVED_INTERNAL_SOURCE_NOT_APPLIED"
  }

} catch {
  $decision = "SCRIPT_ERROR"
  $errors.Add($_.Exception.Message)
  Add-ReportLine "SCRIPT_ERROR: $($_.Exception.Message)"
}

Add-ReportLine ""
Add-ReportLine "## Errors"
if ($errors.Count -eq 0) { Add-ReportLine "none" } else { foreach ($e in $errors) { Add-ReportLine "- $e" } }
Add-ReportLine ""
Add-ReportLine "## Decision"
Add-ReportLine $decision

$out = [ordered]@{
  task_id = $TaskId
  decision = $decision
  report = $Report
  ratecard = $RateCard
  backup = $Backup
  api_log = $ApiLog
  candidate_csv = $CandidateCsv
  errors = @($errors)
  applied = $applied
  row_count_before = $rowCountBefore
  row_count_after = $rowCountAfter
  existing_match_count = $existingMatchCount
  preview_pass = $previewPass
  db_write = $false
  production_deploy = $false
  fake_data = $false
  final_ready_confirmed = $false
}
$out | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $Result
Get-Content $Report -Raw
