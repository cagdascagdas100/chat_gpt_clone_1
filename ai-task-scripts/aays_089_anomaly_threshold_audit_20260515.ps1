$ErrorActionPreference = 'Continue'
$TaskId = 'aays-089-anomaly-threshold-audit-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$DataRoot = 'E:\AAYS_DATA\land_sales'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-089-anomaly-threshold-audit-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'anomaly-threshold-audit.md'
$Csv = Join-Path $DataRoot 'final_outputs\stg_land_sales_50step_db_ready.csv'
$Lines = New-Object System.Collections.Generic.List[string]
function AddLine([string]$m){ [void]$Lines.Add($m) }
function Num($x){ $n=0.0; if([double]::TryParse([string]$x,[ref]$n)){ return $n }; return $null }
function AddRows($title,$rows,$top){
  AddLine ''; AddLine ('## ' + $title)
  AddLine 'verification_id | listing_id | verdict | price | area | ppm | postcode | authority | reason'
  $rows | Select-Object -First $top | ForEach-Object {
    AddLine ($_.verification_id + ' | ' + $_.listing_id + ' | ' + $_.geometry_verdict + ' | ' + $_.ask_price + ' | ' + $_.normalized_area_m2 + ' | ' + $_.price_per_m2 + ' | ' + $_.postcode_standardized + ' | ' + $_.local_authority_standardized + ' | ' + $_.decision_reason)
  }
}
AddLine '# AAYS 089 Anomaly Threshold Audit'
AddLine ('Generated: ' + (Get-Date -Format s))
AddLine ('TaskId: ' + $TaskId)
AddLine ('Csv: ' + $Csv)
AddLine 'Mode: read-only anomaly audit; no DB writes; no UI patch.'
if(!(Test-Path $Csv)){
  AddLine 'ERROR: CSV missing'
  Set-Content -Encoding UTF8 -Path $Report -Value $Lines
  Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
  exit 2
}
try {
  $rows = Import-Csv -Path $Csv
  AddLine ('total_rows: ' + $rows.Count)
  $missingPostcode = $rows | Where-Object { [string]::IsNullOrWhiteSpace($_.postcode_standardized) }
  $missingAuthority = $rows | Where-Object { [string]::IsNullOrWhiteSpace($_.local_authority_standardized) }
  $noPrice = $rows | Where-Object { [string]::IsNullOrWhiteSpace($_.ask_price) }
  $noArea = $rows | Where-Object { [string]::IsNullOrWhiteSpace($_.normalized_area_m2) }
  AddLine ''; AddLine '## Completeness counts'
  AddLine ('missing_postcode: ' + @($missingPostcode).Count)
  AddLine ('missing_authority: ' + @($missingAuthority).Count)
  AddLine ('missing_price: ' + @($noPrice).Count)
  AddLine ('missing_area: ' + @($noArea).Count)
  $withNums = $rows | ForEach-Object {
    $price = Num $_.ask_price; $area = Num $_.normalized_area_m2; $ppm = Num $_.price_per_m2
    $_ | Add-Member -NotePropertyName _price_num -NotePropertyValue $price -Force
    $_ | Add-Member -NotePropertyName _area_num -NotePropertyValue $area -Force
    $_ | Add-Member -NotePropertyName _ppm_num -NotePropertyValue $ppm -Force
    $_
  }
  AddRows 'Largest area candidates' ($withNums | Where-Object { $_._area_num -ne $null } | Sort-Object _area_num -Descending) 15
  AddRows 'Smallest area candidates' ($withNums | Where-Object { $_._area_num -ne $null } | Sort-Object _area_num) 15
  AddRows 'Highest price candidates' ($withNums | Where-Object { $_._price_num -ne $null } | Sort-Object _price_num -Descending) 15
  AddRows 'Lowest price candidates' ($withNums | Where-Object { $_._price_num -ne $null } | Sort-Object _price_num) 15
  AddRows 'Highest price per m2 candidates' ($withNums | Where-Object { $_._ppm_num -ne $null } | Sort-Object _ppm_num -Descending) 15
  $risk = $withNums | Where-Object { ($_.geometry_verdict -eq 'derived_ai_visual') -or ($_.geometry_uncertainty_m -as [double]) -ge 28 -or ($_.verified_polygon_geojson -eq '') } | Select-Object -First 40
  AddRows 'Risk review candidates' $risk 25
  AddLine ''; AddLine '## Suggested threshold review rules'
  AddLine 'rule_area_low_review: normalized_area_m2 < 100'
  AddLine 'rule_area_high_review: normalized_area_m2 > 25000'
  AddLine 'rule_price_high_review: ask_price > 3000000'
  AddLine 'rule_geometry_visual_review: geometry_verdict == derived_ai_visual'
  AddLine 'rule_no_polygon_review: verified_polygon_geojson empty or null'
  AddLine 'wide_accuracy_program_percent: 50'
  AddLine 'AAYS_089_ANOMALY_THRESHOLD_AUDIT_DONE=true'
} catch {
  AddLine ('ERROR: ' + $_.Exception.Message)
}
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_089_ANOMALY_THRESHOLD_AUDIT_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
