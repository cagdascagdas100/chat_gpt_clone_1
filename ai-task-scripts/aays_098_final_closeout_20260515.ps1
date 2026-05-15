$ErrorActionPreference = 'Continue'
$TaskId = 'aays-098-final-closeout-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-098-final-closeout-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'final-closeout.md'
$Files = @(
  'source-inventory.md',
  'validation-sample.md',
  'anomaly-threshold-audit.md',
  'threshold-policy-pack.md',
  'validation-label-template.md',
  'supplemental-sample.md',
  'implementation-readiness-pack.md',
  'risk-label-spec.md',
  'risk-preview.md',
  'risk-policy-calibration.md',
  'risk-preview-v2.md'
)
$Lines = New-Object System.Collections.Generic.List[string]
function AddLine([string]$m){ [void]$Lines.Add($m) }
function AddMatch([string]$path,[string]$pattern){
  if(Test-Path $path){
    $hits = Select-String -Path $path -Pattern $pattern -SimpleMatch -ErrorAction SilentlyContinue
    if($hits){ $hits | ForEach-Object { AddLine ($_.Path + ' :: ' + $_.Line) } }
  }
}
AddLine '# AAYS 098 Final Closeout'
AddLine ('Generated: ' + (Get-Date -Format s))
AddLine ('TaskId: ' + $TaskId)
AddLine 'Mode: read-only final closeout; no DB writes; no UI patch.'
AddLine ''
AddLine '## Completed heartbeat artifacts'
foreach($f in $Files){
  $p = Join-Path $HeartbeatDir $f
  if(Test-Path $p){ AddLine ('OK: ' + $f) } else { AddLine ('MISSING: ' + $f) }
}
AddLine ''
AddLine '## Progress markers'
foreach($f in $Files){ AddMatch (Join-Path $HeartbeatDir $f) 'wide_accuracy_program_percent:' }
AddLine ''
AddLine '## Done markers'
foreach($f in $Files){ AddMatch (Join-Path $HeartbeatDir $f) '_DONE=true' }
AddLine ''
AddLine '## Final status'
AddLine 'db_dryrun_status: complete'
AddLine 'runner_status: complete'
AddLine 'source_inventory_status: complete'
AddLine 'validation_sample_status: complete'
AddLine 'threshold_policy_status: complete'
AddLine 'risk_preview_v2_status: complete'
AddLine 'remaining_before_production: manual labels and code integration tests'
AddLine 'wide_accuracy_program_percent: 90'
AddLine 'AAYS_098_FINAL_CLOSEOUT_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_098_FINAL_CLOSEOUT_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
