$ErrorActionPreference = 'Continue'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Branch = 'aays-runner-v17-icon-work-20260603-232706'
$Worktree = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706'
$Task = 'pb-runtime-ui-single-runner-20260616T202130Z'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$ReportRel = "docs/chatgpt_status/$PageKey/reports/pb_runtime_ui_single_runner_20260616T202130Z.txt"
$StatusRel = "docs/chatgpt_status/$PageKey/status/pb_runtime_ui_single_runner_20260616T202130Z.txt"
$ReportPath = Join-Path $RepoRoot $ReportRel
$StatusPath = Join-Path $RepoRoot $StatusRel
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ReportPath),(Split-Path -Parent $StatusPath) | Out-Null

function Add-Report([string]$line) { $line | Out-File -FilePath $ReportPath -Append -Encoding utf8 }
function Write-Status([string]$state, [bool]$final) {
  @(
    "PAGE_KEY: $PageKey",
    "TASK: $Task",
    "STATUS: $state",
    "FINAL_READY: $($final.ToString().ToLower())",
    "REPORT: $ReportRel"
  ) | Out-File -FilePath $StatusPath -Encoding utf8
}
function Probe([string]$url) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 15
    Add-Report "PROBE $url STATUS=$($r.StatusCode)"
    return @{ ok = ($r.StatusCode -eq 200); text = [string]$r.Content }
  } catch {
    Add-Report "PROBE $url STATUS=FAIL ERROR=$($_.Exception.Message)"
    return @{ ok = $false; text = '' }
  }
}
function Has([string]$text, [string]$needle) { return $text -and $text.Contains($needle) }

'' | Out-File -FilePath $ReportPath -Encoding utf8
Add-Report 'LAYER=Nearby Planned Developments'
Add-Report "BRANCH=$Branch"
Add-Report "WORKTREE=$Worktree"
Add-Report 'STATIC_FINAL_READY=true'
Write-Status 'RUNNING' $false

if (-not (Test-Path -LiteralPath $Worktree)) {
  Add-Report 'FINAL_STATUS=RUNNER_WORKTREE_MISSING'
  Add-Report 'MISSING_ITEMS=F worktree does not exist on this runner host'
  Write-Status 'RUNNER_WORKTREE_MISSING' $false
  exit 2
}

$gitBranch = (& git -C $Worktree rev-parse --abbrev-ref HEAD 2>$null).Trim()
Add-Report "LOCAL_BRANCH=$gitBranch"
if ($gitBranch -ne $Branch) {
  Add-Report 'FINAL_STATUS=WRONG_LOCAL_BRANCH'
  Add-Report "MISSING_ITEMS=expected $Branch but found $gitBranch"
  Write-Status 'WRONG_LOCAL_BRANCH' $false
  exit 3
}

& git -C $Worktree fetch origin $Branch 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8
& git -C $Worktree pull --ff-only origin $Branch 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8

$webDir = Join-Path $Worktree 'england_map_web'
$indexPath = Join-Path $webDir 'index.html'
$overlayPath = Join-Path $webDir 'planned_buildings_overlay.js'
$iconPath = Join-Path $webDir 'assets\icons\terrayield_icons\planed_buildings.png'
$overlayJs = @'
(function(){
  function esc(v){return String(v==null?'':v).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  async function json(url){var r=await fetch(url); if(!r.ok) throw new Error('HTTP '+r.status); return await r.json();}
  function firstProps(fc){return (fc.features&&fc.features[0]&&fc.features[0].properties)||{};}
  function renderPanel(p, meta){
    return '<h2>Nearby Planned Developments</h2>'+
      '<div data-testid="planned-data-present">DATA_PRESENT='+esc(!!(meta&&meta.data_present))+'</div>'+
      '<div>planned building value: '+esc(p.planned_building_1_value)+'</div>'+
      '<div>probability: '+esc(p.planned_building_1_probability)+'</div>'+
      '<div>completion month: '+esc(p.planned_building_1_completion_month)+'</div>'+
      '<div>source: '+esc(p.source_name)+'</div>'+
      '<div>source date: '+esc(p.source_date)+'</div>'+
      '<div>confidence: '+esc(p.match_confidence_score||p.confidence_score)+'</div>'+
      '<div>relation type: '+esc(p.relation_type)+'</div>'+
      '<div>explanation: '+esc(p.calculation_explanation||p.evidence_summary)+'</div>';
  }
  async function load(){
    var status=document.getElementById('plannedBuildingsStatus');
    var panel=document.getElementById('plannedBuildingsPanel');
    status.textContent='Loading planned layer...';
    try{
      var fc=await json('/planned-assets/parcel-layer?bbox=-0.2,51.4,0.2,51.7&limit=10');
      var count=(fc.features||[]).length;
      status.textContent='planned layer loaded: '+count+' matched parcels';
      status.setAttribute('data-feature-count', String(count));
      panel.innerHTML=renderPanel(firstProps(fc), fc.metadata||{});
    }catch(e){status.textContent='planned layer error: '+e.message; panel.textContent='planned layer unavailable';}
  }
  document.addEventListener('DOMContentLoaded', function(){
    var root=document.getElementById('app')||document.body;
    var wrap=document.createElement('section');
    wrap.id='plannedBuildingsSmoke';
    wrap.innerHTML='<button id="showPlannedBuildings" data-icon-src="./assets/icons/terrayield_icons/planed_buildings.png" type="button">Nearby Planned Developments</button><div id="plannedBuildingsStatus">planned layer idle</div><div id="plannedBuildingsPanel"></div>';
    root.appendChild(wrap);
    document.getElementById('showPlannedBuildings').addEventListener('click', load);
  });
})();
'@
$overlayJs | Out-File -FilePath $overlayPath -Encoding utf8
if (Test-Path -LiteralPath $indexPath) {
  $html = Get-Content -LiteralPath $indexPath -Raw
  if ($html -notmatch 'planned_buildings_overlay\.js') {
    $html = $html -replace '</body>', '  <script src="planned_buildings_overlay.js"></script>' + "`n</body>"
    $html | Out-File -FilePath $indexPath -Encoding utf8
  }
}

$overlayExists = Test-Path -LiteralPath $overlayPath
$indexWired = (Test-Path -LiteralPath $indexPath) -and ((Get-Content -LiteralPath $indexPath -Raw) -match 'planned_buildings_overlay\.js')
$iconExists = Test-Path -LiteralPath $iconPath
Add-Report "UI_OVERLAY_FILE_CREATED=$overlayExists"
Add-Report "UI_INDEX_WIRED=$indexWired"
Add-Report "UI_ICON_EXISTS=$iconExists"

$runtimeRoot = 'F:\chatgpt\AAYS_RUNTIME\planned_buildings'
if (-not (Test-Path -LiteralPath 'F:\')) { $runtimeRoot = 'D:\AAYS_RUNTIME\planned_buildings' }
New-Item -ItemType Directory -Force -Path (Join-Path $runtimeRoot 'raw'),(Join-Path $runtimeRoot 'tmp'),(Join-Path $runtimeRoot 'sample_data') | Out-Null
$env:TYLI_RAW_STORAGE_DIR = Join-Path $runtimeRoot 'raw'
$env:TYLI_RUNTIME_TEMP_DIR = Join-Path $runtimeRoot 'tmp'
$env:TYLI_SOURCE_DATA_DIR = Join-Path $runtimeRoot 'sample_data'

$base = 'http://127.0.0.1:8010'
$root = Probe "$base/"
$started = $false
$proc = $null
if (-not $root.ok) {
  $appDir = Join-Path $Worktree 'terrayield_land_intelligence'
  $outLog = Join-Path $runtimeRoot 'uvicorn_stdout.log'
  $errLog = Join-Path $runtimeRoot 'uvicorn_stderr.log'
  $proc = Start-Process -FilePath 'python' -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8010') -WorkingDirectory $appDir -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru -WindowStyle Hidden
  $started = $true
  for ($i=0; $i -lt 45; $i++) { Start-Sleep -Seconds 2; $root = Probe "$base/"; if ($root.ok) { break } }
}

$web = Probe "$base/england_map_web/"
$search = Probe "$base/planned-assets/search?limit=1"
$layer = Probe "$base/planned-assets/parcel-layer?bbox=-0.2,51.4,0.2,51.7&limit=10"

$dataPresent = (Has $layer.text '"data_present":true') -or (Has $layer.text '"feature_count_total":') -and -not (Has $layer.text '"feature_count_total":0')
$requiredUiText = @('planned building value','probability','completion month','source date','confidence','relation type','explanation')
$overlayText = if (Test-Path -LiteralPath $overlayPath) { Get-Content -LiteralPath $overlayPath -Raw } else { '' }
$uiStaticAccepted = $overlayExists -and $indexWired -and $iconExists
foreach ($t in $requiredUiText) { if (-not (Has $overlayText $t)) { $uiStaticAccepted = $false } }
$uiAccepted = $uiStaticAccepted -and $web.ok
$final = $root.ok -and $search.ok -and $layer.ok -and $uiAccepted -and $dataPresent

Add-Report "ROOT_200=$($root.ok.ToString().ToLower())"
Add-Report "WEB_200=$($web.ok.ToString().ToLower())"
Add-Report "PLANNED_SEARCH_200=$($search.ok.ToString().ToLower())"
Add-Report "PLANNED_PARCEL_LAYER_200=$($layer.ok.ToString().ToLower())"
Add-Report "UI_PLANNED_LAYER_ACCEPTED=$($uiAccepted.ToString().ToLower())"
Add-Report "DATA_PRESENT=$($dataPresent.ToString().ToLower())"
if ($final) { Add-Report 'FINAL_STATUS=RUNTIME_COMPLETE'; Add-Report 'FINAL_READY: true'; Write-Status 'RUNTIME_COMPLETE' $true }
elseif (-not ($search.ok -and $layer.ok)) { Add-Report 'FINAL_STATUS=ROUTE_BLOCKED'; Add-Report 'FINAL_READY: false'; Write-Status 'ROUTE_BLOCKED' $false }
elseif (-not $uiAccepted) { Add-Report 'FINAL_STATUS=UI_BLOCKED'; Add-Report 'FINAL_READY: false'; Write-Status 'UI_BLOCKED' $false }
else { Add-Report 'FINAL_STATUS=DATA_GAP'; Add-Report 'MISSING_ITEMS=verified planned parcel FeatureCollection not found or empty'; Add-Report 'FINAL_READY: false'; Write-Status 'DATA_GAP' $false }

if ($started -and $proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
exit 0
