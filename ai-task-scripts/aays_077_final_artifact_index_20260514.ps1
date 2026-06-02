$ErrorActionPreference = 'Continue'
$TaskId = 'aays-077-final-artifact-index-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$RunDir = Join-Path $BridgeRoot 'ai-longruns'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$RunDir,$LogDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss_ffff'
$Report = Join-Path $ResultDir ("aays-077-final-artifact-index-$Stamp.md")
$Heartbeat = Join-Path $HeartbeatDir 'final-artifact-index.md'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
function TableFiles([string]$Title,[string]$Path,[string]$Filter,[int]$Top){
  L ''; L ('## ' + $Title)
  try {
    if(Test-Path $Path){
      $items = Get-ChildItem $Path -Filter $Filter -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First $Top FullName,LastWriteTime,Length
      if($items){ L ($items | Format-Table -AutoSize | Out-String) } else { L 'NO_FILES' }
    } else { L 'MISSING_DIR' }
  } catch { L ('LIST_ERROR: ' + $_.Exception.Message) }
}
function TailFile([string]$Title,[string]$Path,[int]$N){
  L ''; L ('## ' + $Title); L ('Path: ' + $Path)
  if(Test-Path $Path){ try { L '```text'; (Get-Content $Path -Tail $N -ErrorAction SilentlyContinue) | ForEach-Object { L $_ }; L '```' } catch { L ('TAIL_ERROR: ' + $_.Exception.Message) } } else { L 'MISSING' }
}
L '# AAYS 077 Final Artifact Index'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L ('BridgeRoot: ' + $BridgeRoot)
L 'Purpose: index detached worker manifests, recent results, and runner logs without launching new long work.'
TableFiles 'Recent result files' $ResultDir '*' 80
TableFiles 'Recent longrun manifests' $RunDir '*.json' 30
TableFiles 'Recent longrun logs' $RunDir '*.log' 80
TableFiles 'Recent runner logs' $LogDir '*.log' 30
try {
  $manifests = Get-ChildItem $RunDir -Filter '*.json' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 12
  L ''; L '## Manifest status details'
  foreach($m in $manifests){
    L ''; L ('### ' + $m.Name)
    $raw = Get-Content -Raw -Encoding UTF8 $m.FullName
    L '```json'; L $raw; L '```'
    try {
      $obj = $raw | ConvertFrom-Json
      if($obj.pid){
        $p = Get-Process -Id ([int]$obj.pid) -ErrorAction SilentlyContinue
        if($p){ L ('process_status=running pid=' + $obj.pid + ' cpu=' + $p.CPU) } else { L ('process_status=not_running pid=' + $obj.pid) }
      }
      if($obj.stdout){ TailFile ('stdout tail for ' + $m.Name) ([string]$obj.stdout) 60 }
      if($obj.stderr){ TailFile ('stderr tail for ' + $m.Name) ([string]$obj.stderr) 60 }
    } catch { L ('MANIFEST_PARSE_ERROR: ' + $_.Exception.Message) }
  }
} catch { L ('MANIFEST_DETAIL_ERROR: ' + $_.Exception.Message) }
$directHb = Join-Path $HeartbeatDir 'direct-autopilot.md'
TailFile 'Direct autopilot heartbeat' $directHb 80
L ''; L 'AAYS_077_FINAL_ARTIFACT_INDEX_DONE=true'
L 'plan_progress_percent: 100'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_077_FINAL_ARTIFACT_INDEX_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
