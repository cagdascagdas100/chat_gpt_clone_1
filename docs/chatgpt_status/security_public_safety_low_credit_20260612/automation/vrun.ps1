$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$base = Split-Path -Parent $root
$rep = Join-Path $base 'reports'
New-Item -ItemType Directory -Force -Path $rep | Out-Null
$boot = Join-Path $rep 'v_boot.txt'
"state: vrun_started`ntime: $(Get-Date -Format o)`nscript: $root\v.js" | Out-File -FilePath $boot -Encoding utf8
$log = Join-Path $rep 'v_node.log'
try {
  & node (Join-Path $root 'v.js') 2>&1 | Out-File -FilePath $log -Encoding utf8
} catch {
  "state: node_failed`nerror: $($_.Exception.Message)" | Out-File -FilePath (Join-Path $rep 'v_latest.txt') -Encoding utf8
}
if (!(Test-Path (Join-Path $rep 'v_latest.txt'))) {
  "state: no_report`npercent: 99`nfinal: false`nreason: node_finished_without_report" | Out-File -FilePath (Join-Path $rep 'v_latest.txt') -Encoding utf8
}
