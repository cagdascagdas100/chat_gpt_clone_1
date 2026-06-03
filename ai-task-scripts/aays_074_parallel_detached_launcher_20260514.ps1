$ErrorActionPreference = 'Continue'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-074-parallel-detached-launcher-$Stamp.md"
$Launcher = Join-Path $PSScriptRoot 'aays_068_launch_056_detached_unique_20260514.ps1'
$Collector = Join-Path $PSScriptRoot 'aays_070_collect_longruns_status_20260514.ps1'
function AddR([string]$m){ $m | Add-Content -Encoding UTF8 $Report }
'# AAYS 074 Parallel Detached Launcher' | Set-Content -Encoding UTF8 $Report
AddR ('Generated: ' + (Get-Date -Format s))
AddR ('launcher: ' + $Launcher)
AddR ('collector: ' + $Collector)
if(!(Test-Path $Launcher)){ AddR 'ERROR: launcher missing'; exit 2 }
$children = @()
foreach($i in 1..3){
  $out = Join-Path $ResultDir "aays-074-launch-$i-$Stamp.out.log"
  $err = Join-Path $ResultDir "aays-074-launch-$i-$Stamp.err.log"
  $p = Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$Launcher) -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -WindowStyle Hidden
  AddR ("LAUNCHER_$i`_PID=" + $p.Id)
  AddR ("LAUNCHER_$i`_STDOUT=" + $out)
  AddR ("LAUNCHER_$i`_STDERR=" + $err)
  $children += [pscustomobject]@{i=$i; p=$p; out=$out; err=$err}
  Start-Sleep -Seconds 2
}
Start-Sleep -Seconds 10
foreach($c in $children){
  try { $c.p.Refresh(); AddR ("LAUNCHER_$($c.i)_EXITED=" + $c.p.HasExited) } catch { AddR ("LAUNCHER_$($c.i)_REFRESH_ERROR=" + $_.Exception.Message) }
  AddR "## launcher $($c.i) stdout tail"
  if(Test-Path $c.out){ Get-Content $c.out -Tail 80 | Add-Content -Encoding UTF8 $Report }
  AddR "## launcher $($c.i) stderr tail"
  if(Test-Path $c.err){ Get-Content $c.err -Tail 80 | Add-Content -Encoding UTF8 $Report }
}
if(Test-Path $Collector){
  $cout = Join-Path $ResultDir "aays-074-collector-$Stamp.out.log"
  $cerr = Join-Path $ResultDir "aays-074-collector-$Stamp.err.log"
  $cp = Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$Collector) -RedirectStandardOutput $cout -RedirectStandardError $cerr -PassThru -WindowStyle Hidden
  $null = $cp.WaitForExit(120000)
  AddR ('COLLECTOR_EXIT=' + $cp.ExitCode)
  AddR '## collector stdout tail'
  if(Test-Path $cout){ Get-Content $cout -Tail 120 | Add-Content -Encoding UTF8 $Report }
  AddR '## collector stderr tail'
  if(Test-Path $cerr){ Get-Content $cerr -Tail 120 | Add-Content -Encoding UTF8 $Report }
}
AddR 'AAYS_074_PARALLEL_DETACHED_LAUNCHER_DONE=true'
AddR 'plan_progress_percent: 100'
exit 0
