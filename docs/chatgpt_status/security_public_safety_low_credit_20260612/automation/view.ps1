$pageRoot = Split-Path -Parent $PSScriptRoot
$status = Join-Path $pageRoot 'status/security_shared_runner_task_latest.md'
$reportDir = Join-Path $pageRoot 'reports'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$appRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\england_map_web'
$index = Join-Path $appRoot 'index.html'
$screen = Join-Path $reportDir 'security_view_probe.png'
$edge = @('C:\Program Files\Microsoft\Edge\Application\msedge.exe','C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe','C:\Program Files\Google\Chrome\Application\chrome.exe','C:\Program Files (x86)\Google\Chrome\Application\chrome.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1
$okIndex = Test-Path $index
$rendered = $false
if ($okIndex -and $edge) {
  $url = 'file:///' + ($index -replace '\\','/')
  $args = "--headless --disable-gpu --window-size=1600,1000 --screenshot=$screen $url"
  $p = Start-Process -FilePath $edge -ArgumentList $args -PassThru -Wait
  if (Test-Path $screen) { $rendered = $true }
}
$state = 'view_probe_done'
$percent = '99'
$final = 'false'
$reason = 'render_missing'
if ($rendered) { $reason = 'interactive_click_needed' }
$content = "state: $state`npercent: $percent`nfinal: $final`nreason: $reason`nindex: $okIndex`nviewer: $edge`nrendered: $rendered`nscreenshot: $screen"
Set-Content -Path $status -Value $content -Encoding UTF8
Set-Content -Path (Join-Path $reportDir 'security_view_probe_latest.txt') -Value $content -Encoding UTF8
Write-Output $content
