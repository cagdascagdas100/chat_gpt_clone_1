$ErrorActionPreference = 'Continue'
$TaskId = 'aays-083-wide-accuracy-gap-audit-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss_ffff'
$Report = Join-Path $ResultDir ("aays-083-wide-accuracy-gap-audit-$Stamp.md")
$Heartbeat = Join-Path $HeartbeatDir 'wide-accuracy-gap-audit.md'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
function AddFiles($Title,$Path,$Filter,$Top){
  L ''; L ('## ' + $Title)
  if(Test-Path $Path){
    try { $items = Get-ChildItem $Path -Recurse -File -Filter $Filter -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First $Top FullName,LastWriteTime,Length; if($items){ L ($items | Format-Table -AutoSize | Out-String) } else { L 'NO_FILES' } } catch { L ('LIST_ERROR: ' + $_.Exception.Message) }
  } else { L 'MISSING_DIR: ' + $Path }
}
function GrepLite($Title,$Path,$Pattern,$Top){
  L ''; L ('## ' + $Title)
  if(Test-Path $Path){
    try { $hits = Get-ChildItem $Path -Recurse -File -Include *.py,*.ps1,*.js,*.ts,*.tsx,*.json,*.md,*.yml,*.yaml -ErrorAction SilentlyContinue | Select-String -Pattern $Pattern -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First $Top Path,LineNumber,Line; if($hits){ L ($hits | Format-Table -AutoSize | Out-String) } else { L 'NO_HITS' } } catch { L ('GREP_ERROR: ' + $_.Exception.Message) }
  } else { L 'MISSING_DIR: ' + $Path }
}
L '# AAYS 083 Wide Accuracy Gap Audit'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L ('BridgeRoot: ' + $BridgeRoot)
L ('ProjectRoot: ' + $ProjectRoot)
L 'Mode: read-only audit; no DB writes; no UI patch.'
AddFiles 'Recent bridge results' $ResultDir '*' 40
AddFiles 'Project data candidates csv' $ProjectRoot '*.csv' 30
AddFiles 'Project data candidates geojson' $ProjectRoot '*.geojson' 30
AddFiles 'Project scripts python' $ProjectRoot '*.py' 40
AddFiles 'Project config files' $ProjectRoot '*.json' 30
GrepLite 'Endpoint/API clues' $ProjectRoot 'FastAPI' 40
GrepLite 'Parcel clues' $ProjectRoot 'parcel' 80
GrepLite 'Land sale clues' $ProjectRoot 'land' 80
GrepLite 'TODO/FIXME clues' $ProjectRoot 'TODO' 80
GrepLite 'Error/exception clues' $ProjectRoot 'Exception' 80
L ''; L '## Initial score baseline carried forward'
L 'source_accuracy_score_estimate: 45/100'
L 'parcel_match_accuracy_score_estimate: 27/100'
L 'operational_health_score_estimate: 0/100 before runner recovery; runner channel now healthy after single-instance fix'
L 'general_confidence_score_estimate: 32/100 baseline; audit output will identify next improvement targets'
L ''; L '## Next improvement targets'
L '1. Confirm authoritative source datasets and schema map.'
L '2. Build parcel matching validation sample with expected matches/non-matches.'
L '3. Add endpoint health probes and regression checks.'
L '4. Separate long DB/import jobs from main runner; keep collector-only status tasks in current-task.'
L 'AAYS_083_WIDE_ACCURACY_GAP_AUDIT_DONE=true'
L 'plan_progress_percent: 100 runner; 36 wide accuracy program'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_083_WIDE_ACCURACY_GAP_AUDIT_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
