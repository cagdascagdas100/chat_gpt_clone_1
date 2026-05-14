$ErrorActionPreference = 'Continue'
$TaskId = 'aays-070-collect-longruns-status-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$RunDir = Join-Path $BridgeRoot 'ai-longruns'
New-Item -ItemType Directory -Force -Path $ResultDir,$RunDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss_ffff'
$Report = Join-Path $ResultDir ("aays-070-longruns-status-$Stamp.md")
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
function AddTail([string]$Path,[int]$N){ if(Test-Path $Path){ try { (Get-Content $Path -Tail $N -ErrorAction SilentlyContinue) | ForEach-Object { L $_ } } catch { L ('TAIL_ERROR: ' + $_.Exception.Message) } } else { L 'MISSING' } }
L '# AAYS 070 Longruns Status Collector'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L ''
L '## Manifest files'
$manifests = @()
try { $manifests = Get-ChildItem $RunDir -Filter '*.json' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 10 } catch { L ('MANIFEST_LIST_ERROR: ' + $_.Exception.Message) }
if($manifests.Count -eq 0){ L 'NO_MANIFESTS_FOUND' }
foreach($m in $manifests){
  L ''
  L ('### ' + $m.Name)
  L ('LastWriteTime: ' + $m.LastWriteTime.ToString('s'))
  try {
    $raw = Get-Content -Raw -Encoding UTF8 $m.FullName
    L '```json'
    L $raw
    L '```'
    $obj = $raw | ConvertFrom-Json
    if($obj.pid){
      $p = Get-Process -Id ([int]$obj.pid) -ErrorAction SilentlyContinue
      if($p){ L ('process_status: running pid=' + $obj.pid + ' cpu=' + $p.CPU) } else { L ('process_status: not_running pid=' + $obj.pid) }
    }
    if($obj.stdout){ L ''; L '#### stdout tail'; AddTail ([string]$obj.stdout) 80 }
    if($obj.stderr){ L ''; L '#### stderr tail'; AddTail ([string]$obj.stderr) 80 }
  } catch { L ('MANIFEST_READ_ERROR: ' + $_.Exception.Message) }
}
L ''
L '## Recent result files'
try { $items = Get-ChildItem $ResultDir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 20 Name,LastWriteTime,Length; L ($items | Format-Table -AutoSize | Out-String) } catch { L ('RESULT_LIST_ERROR: ' + $_.Exception.Message) }
L ''
L 'AAYS_070_LONGRUNS_STATUS_COLLECTOR_DONE=true'
L 'plan_progress_percent: 100'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Write-Output 'AAYS_070_LONGRUNS_STATUS_COLLECTOR_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
