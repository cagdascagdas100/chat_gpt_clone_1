$ErrorActionPreference = "Continue"
Set-StrictMode -Version Latest

$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$OutDir = Join-Path $BridgeRoot "ai-results"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$TaskId = "cost12-preview-400-diagnose-readonly-20260525"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Report = Join-Path $OutDir "cost12_preview_400_diagnose_readonly_$Stamp.md"
$Result = Join-Path $OutDir "cost12_preview_400_diagnose_readonly.result.json"
$ApiJsonl = Join-Path $OutDir "cost12_preview_400_payload_matrix_$Stamp.jsonl"

$RateCard = Join-Path $ProjectRoot "tools\cost_uk_real_engine\config\building_type_rate_card_uk.csv"
$Service = Join-Path $ProjectRoot "app\services\cost_engine_service.py"
$Schema = Join-Path $ProjectRoot "app\schemas\cost.py"

function Add-Line([string]$line) { $line | Add-Content -Encoding UTF8 $Report }
function Invoke-Preview($name, $bodyObj) {
  $json = $bodyObj | ConvertTo-Json -Depth 20
  $record = [ordered]@{ name=$name; ok=$false; status_code=$null; body=$null; error=$null; request=$bodyObj }
  try {
    $resp = Invoke-WebRequest -Method Post -Uri "http://127.0.0.1:8010/cost/estimate/preview" -ContentType "application/json" -Body $json -UseBasicParsing -TimeoutSec 60
    $record.ok = $true
    $record.status_code = [int]$resp.StatusCode
    $record.body = $resp.Content
  } catch {
    $record.error = $_.Exception.Message
    try {
      if ($_.Exception.Response) {
        $record.status_code = [int]$_.Exception.Response.StatusCode
        $stream = $_.Exception.Response.GetResponseStream()
        if ($stream) {
          $reader = New-Object System.IO.StreamReader($stream)
          $record.body = $reader.ReadToEnd()
        }
      }
    } catch {}
    if (-not $record.body -and $_.ErrorDetails) { $record.body = $_.ErrorDetails.Message }
  }
  ($record | ConvertTo-Json -Depth 30 -Compress) | Add-Content -Encoding UTF8 $ApiJsonl
  return $record
}

"# COST12 Preview 400 Diagnose Read-only" | Set-Content -Encoding UTF8 $Report
Add-Line "time=$Stamp"
Add-Line "task_id=$TaskId"
Add-Line "db_write=false"
Add-Line "production_deploy=false"
Add-Line "fake_data=false"
Add-Line ""

$errors = New-Object System.Collections.Generic.List[string]
$matrix = @()
$decision = "UNKNOWN"

Add-Line "## Rate-card inspection"
if (Test-Path $RateCard) {
  $rows = @(Import-Csv $RateCard)
  Add-Line "ratecard=$RateCard"
  Add-Line "row_count=$($rows.Count)"
  if ($rows.Count -gt 0) {
    Add-Line "headers=$($rows[0].PSObject.Properties.Name -join ',')"
  }
  $retail = @($rows | Where-Object { $_.building_type -eq "retail" })
  Add-Line "retail_rows=$($retail.Count)"
  $retailMid = @($retail | Where-Object { ($_.spec_grade -eq "mid" -or $_.quality_level -eq "mid" -or $_.grade -eq "mid") -and ($_.region -eq "UK") -and ($_.scenario_version -eq "cost_uk_v1" -or $_.scenario -eq "cost_uk_v1") })
  Add-Line "retail_mid_uk_cost_uk_v1_rows=$($retailMid.Count)"
  foreach ($r in $retailMid | Select-Object -First 5) {
    Add-Line "MATCH_ROW: $($r | ConvertTo-Json -Compress -Depth 10)"
  }
} else {
  $errors.Add("missing_ratecard:$RateCard")
  Add-Line "missing_ratecard=$RateCard"
}

Add-Line ""
Add-Line "## Service snippets"
if (Test-Path $Service) {
  Add-Line "service=$Service"
  Select-String -Path $Service -Pattern "No cost rate row found","_pick_rate_row","base_rate_gbp_per_gia_m2","spec_grade","scenario_version","source_reliability","production_ready_candidate" -SimpleMatch -Context 6,12 -ErrorAction SilentlyContinue |
    Select-Object -First 120 |
    ForEach-Object {
      Add-Line "### $($_.Path):$($_.LineNumber)"
      Add-Line ($_.Context.PreContext -join "`n")
      Add-Line $_.Line
      Add-Line ($_.Context.PostContext -join "`n")
    }
} else { $errors.Add("missing_service:$Service") }

Add-Line ""
Add-Line "## Schema snippets"
if (Test-Path $Schema) {
  Add-Line "schema=$Schema"
  Select-String -Path $Schema -Pattern "CostEstimate","gross_internal_area_m2","quality_level","building_subtype","fit_out_level","cooling_kitchen_need","sales_area_m2" -SimpleMatch -Context 4,10 -ErrorAction SilentlyContinue |
    Select-Object -First 80 |
    ForEach-Object {
      Add-Line "### $($_.Path):$($_.LineNumber)"
      Add-Line ($_.Context.PreContext -join "`n")
      Add-Line $_.Line
      Add-Line ($_.Context.PostContext -join "`n")
    }
} else { $errors.Add("missing_schema:$Schema") }

Add-Line ""
Add-Line "## API payload matrix"
$base = @{
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
}
$matrix += Invoke-Preview "retail_restaurant_mid_full" $base

$b2 = $base.Clone(); $b2.building_subtype = "small_shop"; $matrix += Invoke-Preview "retail_small_shop_mid_full" $b2
$b3 = $base.Clone(); $b3.Remove("building_subtype"); $matrix += Invoke-Preview "retail_mid_no_subtype" $b3
$b4 = $base.Clone(); $b4.quality_level = "default"; $matrix += Invoke-Preview "retail_restaurant_default" $b4
$b5 = $base.Clone(); $b5.Remove("sales_area_m2"); $matrix += Invoke-Preview "retail_no_sales_area" $b5

foreach ($m in $matrix) {
  Add-Line "### $($m.name)"
  Add-Line "ok=$($m.ok) status=$($m.status_code) error=$($m.error)"
  Add-Line "body=$($m.body)"
}

$passCount = @($matrix | Where-Object { $_.ok -eq $true -and $_.status_code -ge 200 -and $_.status_code -lt 300 }).Count
$badRequestBodies = @($matrix | Where-Object { $_.status_code -eq 400 } | ForEach-Object { $_.body })

if ($passCount -gt 0) { $decision = "PREVIEW_PASS_WITH_ALTERNATIVE_PAYLOAD" }
elseif (($badRequestBodies -join "`n") -match "No cost rate row found") { $decision = "PREVIEW_400_RATE_ROW_STILL_NOT_MATCHED" }
elseif (($badRequestBodies -join "`n") -match "parcel|Parcel|not found") { $decision = "PREVIEW_400_PARCEL_OR_DB_DATA_ISSUE" }
elseif ($matrix.Count -gt 0) { $decision = "PREVIEW_400_UNKNOWN_BODY_CAPTURED" }
else { $decision = "DIAGNOSE_FAILED" }

Add-Line ""
Add-Line "## Decision"
Add-Line $decision
Add-Line "api_jsonl=$ApiJsonl"

$out = [ordered]@{
  task_id=$TaskId
  decision=$decision
  report=$Report
  api_jsonl=$ApiJsonl
  errors=@($errors)
  pass_count=$passCount
  db_write=$false
  production_deploy=$false
  fake_data=$false
}
$out | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $Result
Get-Content $Report -Raw
