$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$base = Split-Path -Parent $root
$rep = Join-Path $base 'reports'
New-Item -ItemType Directory -Force -Path $rep | Out-Null
$out = Join-Path $rep 'v_latest.txt'
$boot = Join-Path $rep 'v_boot.txt'
"state: ps_probe_started`ntime: $(Get-Date -Format o)" | Out-File -FilePath $boot -Encoding utf8
$appRoots = @(
  'C:\Users\cagda\Documents\GitHub\AAYS\england_map_web',
  'C:\AAYS_GITHUB_BRIDGE_CLEAN2\england_map_web',
  'C:\AAYS_GITHUB_BRIDGE_CLEAN2\terrayield_land_intelligence\england_map_web'
)
$app = $null
foreach ($r in $appRoots) { if (Test-Path (Join-Path $r 'index.html')) { $app = $r; break } }
$edgePaths = @(
  'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
  'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
  'C:\Program Files\Google\Chrome\Application\chrome.exe',
  'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
)
$browser = $null
foreach ($b in $edgePaths) { if (Test-Path $b) { $browser = $b; break } }
$index = if ($app) { Test-Path (Join-Path $app 'index.html') } else { $false }
$appjs = if ($app) { Test-Path (Join-Path $app 'app.js') } else { $false }
$overlay = if ($app) { Test-Path (Join-Path $app 'security_overlay.js') } else { $false }
$data = if ($app) { Test-Path (Join-Path $app 'data\parcel_security_scores_rechecked_0_120m_spatial.geojson') } else { $false }
$txt = if ($appjs) { Get-Content -Raw -Path (Join-Path $app 'app.js') } else { '' }
$ovtxt = if ($overlay) { Get-Content -Raw -Path (Join-Path $app 'security_overlay.js') } else { '' }
$contract = ($txt -match 'security\.png') -and ($txt -match 'AAYS_SECURITY') -and ($ovtxt -match 'parcel_security_scores_rechecked_0_120m_spatial')
$shot = $false
if ($browser -and $index) {
  $shotPath = Join-Path $rep 'v_ps_view.png'
  $url = 'file:///' + ((Join-Path $app 'index.html') -replace '\\','/')
  $args = @('--headless=new','--disable-gpu','--no-first-run',"--screenshot=$shotPath",$url)
  $p = Start-Process -FilePath $browser -ArgumentList $args -PassThru -WindowStyle Hidden
  Wait-Process -Id $p.Id -Timeout 30 -ErrorAction SilentlyContinue
  $shot = Test-Path $shotPath
}
$ready = $index -and $appjs -and $overlay -and $data -and $contract -and $shot
$percent = if ($ready) { 99 } else { 97 }
$reason = if ($ready) { 'static_render_ready_click_popup_needed' } else { 'preflight_incomplete' }
@(
  'state: ps_probe_done',
  "percent: $percent",
  'final: false',
  "reason: $reason",
  "app: $app",
  "browser: $browser",
  "index: $index",
  "appjs: $appjs",
  "overlay: $overlay",
  "data: $data",
  "contract: $contract",
  "shot: $shot"
) | Out-File -FilePath $out -Encoding utf8
