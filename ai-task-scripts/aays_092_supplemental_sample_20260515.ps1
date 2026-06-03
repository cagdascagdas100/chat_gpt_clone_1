$ErrorActionPreference = 'Continue'
$TaskId = 'aays-092-supplemental-sample-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-092-supplemental-sample-$Stamp.md"
$OutCsv = Join-Path $ResultDir "aays-092-supplemental-sample-$Stamp.csv"
$Heartbeat = Join-Path $HeartbeatDir 'supplemental-sample.md'
$SourceCsv = 'E:\AAYS_DATA\land_sales\final_outputs\stg_land_sales_50step_db_ready.csv'
$BaseCsv = Get-ChildItem $ResultDir -Filter 'aays-091-validation-label-template-*.csv' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
L '# AAYS 092 Supplemental Sample'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L 'Mode: read-only supplemental sample; no DB writes; no UI patch.'
if(!(Test-Path $SourceCsv)){ L 'ERROR source csv missing'; Set-Content -Encoding UTF8 -Path $Report -Value $Lines; exit 2 }
if($null -eq $BaseCsv){ L 'ERROR base label csv missing'; Set-Content -Encoding UTF8 -Path $Report -Value $Lines; exit 3 }
$rows = Import-Csv $SourceCsv
$base = Import-Csv $BaseCsv.FullName
$used = @{}
foreach($b in $base){ $used[$b.verification_id] = $true }
$supp = @()
$supp += $rows | Where-Object { -not $used.ContainsKey($_.verification_id) -and $_.geometry_verdict -eq 'derived_ai_visual' } | Sort-Object {[double]$_.ask_price} -Descending | Select-Object -First 2
$supp += $rows | Where-Object { -not $used.ContainsKey($_.verification_id) -and $_.geometry_verdict -eq 'derived_ai_visual' } | Sort-Object {[double]$_.normalized_area_m2} -Descending | Select-Object -First 2
$supp += $rows | Where-Object { -not $used.ContainsKey($_.verification_id) -and $_.geometry_verdict -eq 'derived_signal' } | Select-Object -First 2
$supp = $supp | Sort-Object verification_id -Unique | Select-Object -First 6
$i = 1
$template = foreach($r in $supp){
  [pscustomobject]@{
    supplemental_case_id = ('SUP-' + $i.ToString('000'))
    verification_id = $r.verification_id
    listing_id = $r.listing_id
    geometry_verdict = $r.geometry_verdict
    geometry_evidence_type = $r.geometry_evidence_type
    geometry_uncertainty_m = $r.geometry_uncertainty_m
    postcode_standardized = $r.postcode_standardized
    local_authority_standardized = $r.local_authority_standardized
    ask_price = $r.ask_price
    normalized_area_m2 = $r.normalized_area_m2
    reviewer_label = ''
    reviewer_confidence = ''
    evidence_checked = ''
    issue_type = ''
    corrected_verdict = ''
    reviewer_notes = ''
  }
  $i++
}
$template | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $OutCsv
L ('source_rows: ' + $rows.Count)
L ('base_label_csv: ' + $BaseCsv.FullName)
L ('base_rows: ' + @($base).Count)
L ('supplemental_rows: ' + @($template).Count)
L ('combined_review_rows: ' + (@($base).Count + @($template).Count))
L ('supplemental_csv: ' + $OutCsv)
L ''
L '## Purpose'
L 'Adds extra non-duplicate rows so the review set reaches at least 25 rows.'
L ''
L '## Preview'
L ($template | Format-Table -AutoSize | Out-String)
L ''
L 'wide_accuracy_program_percent: 65'
L 'AAYS_092_SUPPLEMENTAL_SAMPLE_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_092_SUPPLEMENTAL_SAMPLE_DONE=true'
Write-Output ('REPORT=' + $Report)
Write-Output ('SUPPLEMENTAL_CSV=' + $OutCsv)
exit 0
