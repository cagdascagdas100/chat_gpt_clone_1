$r=Split-Path -Parent $PSScriptRoot
$d=Join-Path $r 'reports'
$s=Join-Path $r 'status/security_shared_runner_task_latest.md'
New-Item -ItemType Directory -Force -Path $d | Out-Null
$a='C:\Users\cagda\Documents\GitHub\AAYS\england_map_web'
$i=Test-Path (Join-Path $a 'index.html')
$j=Test-Path (Join-Path $a 'app.js')
$o=Test-Path (Join-Path $a 'security_overlay.js')
$g=Test-Path (Join-Path $a 'data/parcel_security_scores_rechecked_0_120m_spatial.geojson')
$m=(Test-Path (Join-Path $a 'data/parcel_security_scores_rechecked_0_120m_spatial.summary.json')) -or (Test-Path (Join-Path $a 'data/parcel_security_scores_summary.json'))
$x=Test-Path (Join-Path $d 'security_view_probe.png')
$c="state: q_done`npercent: 99`nfinal: false`nreason: final_click_needed`nindex: $i`napp: $j`noverlay: $o`ndata: $g`nsummary: $m`nshot: $x"
Set-Content -Path $s -Value $c -Encoding UTF8
Set-Content -Path (Join-Path $d 'q_latest.txt') -Value $c -Encoding UTF8
Write-Output $c
