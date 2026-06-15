$r=Split-Path -Parent $PSScriptRoot
$d=Join-Path $r 'reports'
$s=Join-Path $r 'status/security_shared_runner_task_latest.md'
New-Item -ItemType Directory -Force -Path $d | Out-Null
$a='C:\Users\cagda\Documents\GitHub\AAYS\england_map_web'
$i=Join-Path $a 'index.html'
$edge=@('C:\Program Files\Microsoft\Edge\Application\msedge.exe','C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')|Where-Object{Test-Path $_}|Select-Object -First 1
$started=$false
$shot2=Join-Path $d 'z_view.png'
if((Test-Path $i) -and $edge){
  $url='file:///'+($i -replace '\\','/')
  Start-Process -FilePath $edge -ArgumentList "--new-window $url"
  Start-Sleep -Seconds 5
  $started=$true
  Add-Type -AssemblyName System.Windows.Forms
  [System.Windows.Forms.SendKeys]::SendWait('{TAB}{TAB}{ENTER}')
  Start-Sleep -Seconds 3
  $args="--headless --disable-gpu --window-size=1600,1000 --screenshot=$shot2 $url"
  Start-Process -FilePath $edge -ArgumentList $args -Wait
}
$ok=Test-Path $shot2
$c="state: z_done`npercent: 99`nfinal: false`nreason: runtime_visual_review_needed`nopened: $started`nshot2: $ok`nshot2_path: $shot2"
Set-Content -Path $s -Value $c -Encoding UTF8
Set-Content -Path (Join-Path $d 'z_latest.txt') -Value $c -Encoding UTF8
Write-Output $c
