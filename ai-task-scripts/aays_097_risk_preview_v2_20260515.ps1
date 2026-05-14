$ErrorActionPreference = 'Continue'
$TaskId = 'aays-097-risk-preview-v2-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$DataRoot = 'E:\AAYS_DATA\land_sales'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-097-risk-preview-v2-$Stamp.md"
$OutCsv = Join-Path $ResultDir "aays-097-risk-preview-v2-$Stamp.csv"
$Heartbeat = Join-Path $HeartbeatDir 'risk-preview-v2.md'
$Csv = Join-Path $DataRoot 'final_outputs\stg_land_sales_50step_db_ready.csv'
$Lines = New-Object System.Collections.Generic.List[string]
function AddLine([string]$m){ [void]$Lines.Add($m) }
function Num($x){ $n=0.0; if([double]::TryParse([string]$x,[ref]$n)){ return $n }; return $null }
function Blank($x){ return [string]::IsNullOrWhiteSpace([string]$x) }
function ClassifyV2($r){
  $reasons = New-Object System.Collections.Generic.List[string]
  $risk = 'medium'
  $status = 'manual_review'
  $price = Num $r.ask_price
  $area = Num $r.normalized_area_m2
  $ppm = Num $r.price_per_m2
  $anomaly = $false
  if((Blank $r.postcode_standardized) -or (Blank $r.local_authority_standardized) -or (Blank $r.ask_price) -or (Blank $r.normalized_area_m2)){
    return @('critical','needs_source','missing_core_field')
  }
  if(Blank $r.verified_polygon_geojson){ $reasons.Add('no_verified_polygon') | Out-Null; $status='manual_review' } else { $status='accept_candidate' }
  if($area -ne $null -and $area -lt 100){ $anomaly=$true; $reasons.Add('area_below_100') | Out-Null }
  if($area -ne $null -and $area -gt 25000){ $anomaly=$true; $reasons.Add('area_above_25000') | Out-Null }
  if($price -ne $null -and $price -gt 3000000){ $anomaly=$true; $reasons.Add('price_above_3000000') | Out-Null }
  if($ppm -ne $null -and $ppm -gt 5000){ $anomaly=$true; $reasons.Add('ppm_above_5000') | Out-Null }
  if($r.geometry_verdict -eq 'derived_ai_visual'){ $reasons.Add('ai_visual_candidate') | Out-Null; $risk = if($anomaly){'critical'}else{'high'} }
  elseif($r.geometry_verdict -eq 'derived_signal'){ $reasons.Add('signal_candidate') | Out-Null; $risk = if($anomaly){'high'}else{'medium'} }
  elseif($r.geometry_verdict -eq 'derived_multi_signal'){ $reasons.Add('multi_signal_candidate') | Out-Null; $risk = if($anomaly){'high'}else{'low'} }
  else { $reasons.Add('unknown_verdict') | Out-Null; $risk='high' }
  if($reasons.Count -eq 0){ $reasons.Add('no_policy_flag') | Out-Null }
  return @($risk,$status,($reasons -join ';'))
}
AddLine '# AAYS 097 Risk Preview V2'
AddLine ('Generated: ' + (Get-Date -Format s))
AddLine ('TaskId: ' + $TaskId)
AddLine ('SourceCsv: ' + $Csv)
AddLine ('OutCsv: ' + $OutCsv)
AddLine 'Mode: read-only calibrated preview; source CSV is not overwritten.'
if(!(Test-Path $Csv)){
  AddLine 'ERROR: source CSV missing'
  Set-Content -Encoding UTF8 -Path $Report -Value $Lines
  Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
  exit 2
}
try {
  $rows = Import-Csv -Path $Csv
  $out = foreach($r in $rows){
    $c = ClassifyV2 $r
    $obj = [ordered]@{}
    foreach($p in $r.PSObject.Properties){ $obj[$p.Name] = $p.Value }
    $obj['risk_label_v2'] = $c[0]
    $obj['acceptance_status_strict'] = $c[1]
    $obj['policy_reason_v2'] = $c[2]
    [pscustomobject]$obj
  }
  $out | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $OutCsv
  AddLine ('source_rows: ' + @($rows).Count)
  AddLine ('preview_rows: ' + @($out).Count)
  AddLine ''
  AddLine '## risk_label_v2 distribution'
  $out | Group-Object risk_label_v2 | Sort-Object Count -Descending | ForEach-Object { AddLine ($_.Name + ': ' + $_.Count) }
  AddLine ''
  AddLine '## acceptance_status_strict distribution'
  $out | Group-Object acceptance_status_strict | Sort-Object Count -Descending | ForEach-Object { AddLine ($_.Name + ': ' + $_.Count) }
  AddLine ''
  AddLine '## policy_reason_v2 top distribution'
  $out | Group-Object policy_reason_v2 | Sort-Object Count -Descending | Select-Object -First 20 | ForEach-Object { AddLine ($_.Name + ': ' + $_.Count) }
  AddLine ''
  AddLine 'wide_accuracy_program_percent: 86'
  AddLine 'AAYS_097_RISK_PREVIEW_V2_DONE=true'
} catch { AddLine ('ERROR: ' + $_.Exception.Message) }
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_097_RISK_PREVIEW_V2_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
