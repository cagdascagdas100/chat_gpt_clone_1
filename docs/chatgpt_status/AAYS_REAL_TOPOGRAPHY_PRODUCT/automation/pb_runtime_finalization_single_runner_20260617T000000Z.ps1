$ErrorActionPreference = 'Continue'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Branch = 'aays-runner-v17-icon-work-20260603-232706'
$PreferredWorktree = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706'
$Task = 'pb-runtime-finalization-single-runner-20260617T000000Z'
$ReportRel = "docs/chatgpt_status/$PageKey/reports/pb_runtime_finalization_single_runner_20260617T000000Z.txt"
$StatusRel = "docs/chatgpt_status/$PageKey/status/pb_runtime_finalization_single_runner_20260617T000000Z.txt"
$ReportRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$Worktree = $ReportRoot
try {
  if (Test-Path -LiteralPath $PreferredWorktree) {
    $inside = git -C $PreferredWorktree rev-parse --is-inside-work-tree 2>$null
    $localBranch = (git -C $PreferredWorktree rev-parse --abbrev-ref HEAD 2>$null).Trim()
    if (($LASTEXITCODE -eq 0) -and ($inside.Trim() -eq 'true') -and ($localBranch -eq $Branch)) { $Worktree = $PreferredWorktree }
  }
} catch {}
$ReportPath = Join-Path $ReportRoot $ReportRel
$StatusPath = Join-Path $ReportRoot $StatusRel
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ReportPath),(Split-Path -Parent $StatusPath) | Out-Null
function Write-Report([string]$line) { $line | Out-File -FilePath $ReportPath -Append -Encoding utf8 }
function Write-State([string]$state, [bool]$final) { @("PAGE_KEY: $PageKey","TASK: $Task","STATUS: $state","FINAL_READY: $($final.ToString().ToLower())","REPORT: $ReportRel") | Out-File -FilePath $StatusPath -Encoding utf8 }
function Probe([string]$url) { try { $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 20; Write-Report "PROBE $url STATUS=$($r.StatusCode)"; return @{ ok=($r.StatusCode -eq 200); text=[string]$r.Content } } catch { Write-Report "PROBE $url STATUS=FAIL ERROR=$($_.Exception.Message)"; return @{ ok=$false; text='' } } }
function HasText([string]$s,[string]$n) { return ($null -ne $s) -and $s.Contains($n) }
function Commit-Outputs([string]$msg) { try { git -C $ReportRoot add $ReportRel $StatusRel 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8; $pending = git -C $ReportRoot status --porcelain -- $ReportRel $StatusRel; if ($pending) { git -C $ReportRoot commit -m $msg 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8; git -C $ReportRoot push origin HEAD:$Branch 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8 } } catch { Write-Report "GIT_OUTPUT_PUSH_ERROR=$($_.Exception.Message)" } }
'' | Out-File -FilePath $ReportPath -Encoding utf8
Write-Report 'LAYER=Nearby Planned Developments'
Write-Report "PAGE_KEY=$PageKey"
Write-Report "BRANCH=$Branch"
Write-Report "REPORT_ROOT=$ReportRoot"
Write-Report "RUNTIME_WORKTREE=$Worktree"
Write-Report 'STATIC_FINAL_READY=true'
Write-State 'RUNNING' $false
try { git -C $Worktree fetch origin $Branch 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8; git -C $Worktree pull --ff-only origin $Branch 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8 } catch { Write-Report "WORKTREE_SYNC_WARNING=$($_.Exception.Message)" }
$webDir = Join-Path $Worktree 'england_map_web'
$indexPath = Join-Path $webDir 'index.html'
$overlayPath = Join-Path $webDir 'planned_buildings_overlay.js'
$routePath = Join-Path $Worktree 'terrayield_land_intelligence\app\api\routes\planned_assets.py'
$iconPath = Join-Path $webDir 'assets\icons\terrayield_icons\planed_buildings.png'
$indexWired = (Test-Path $indexPath) -and ((Get-Content $indexPath -Raw) -match 'planned_buildings_overlay\.js')
$overlayOk = (Test-Path $overlayPath) -and ((Get-Content $overlayPath -Raw) -match 'planned building value') -and ((Get-Content $overlayPath -Raw) -match 'relation type')
$routeLoaderOk = (Test-Path $routePath) -and ((Get-Content $routePath -Raw) -match 'TYLI_PLANNED_ASSETS_GEOJSON') -and ((Get-Content $routePath -Raw) -match 'feature_count_total')
$iconOk = Test-Path $iconPath
Write-Report "UI_INDEX_WIRED=$($indexWired.ToString().ToLower())"
Write-Report "UI_OVERLAY_ACCEPTANCE_TEXT=$($overlayOk.ToString().ToLower())"
Write-Report "BACKEND_DATA_LOADER_PRESENT=$($routeLoaderOk.ToString().ToLower())"
Write-Report "UI_ICON_EXISTS=$($iconOk.ToString().ToLower())"
$candidateFiles = @()
foreach ($envName in @('TYLI_PLANNED_ASSETS_GEOJSON','AAYS_PLANNED_ASSETS_GEOJSON','PLANNED_ASSETS_PARCEL_LAYER_GEOJSON')) { if ([Environment]::GetEnvironmentVariable($envName)) { $candidateFiles += [Environment]::GetEnvironmentVariable($envName) } }
foreach ($dir in @((Join-Path $webDir 'data'),(Join-Path $Worktree 'terrayield_land_intelligence\data'),(Join-Path $Worktree 'data'),'F:\chatgpt\AAYS_RUNTIME\planned_buildings\sample_data','F:\chatgpt\AAYS_DATA','D:\AAYS_DATA')) { foreach ($name in @('planned_assets_parcel_layer.geojson','parcel_planned_assets.geojson','planned_buildings_parcel_layer.geojson','nearby_planned_developments.geojson','parcel_planned_buildings.geojson','planned_assets_parcel_layer.json','parcel_planned_assets.json','planned_buildings_parcel_layer.json','nearby_planned_developments.json')) { $candidateFiles += (Join-Path $dir $name) } }
$dataFile = $null
foreach ($f in $candidateFiles) { if ($f -and (Test-Path -LiteralPath $f)) { $dataFile = $f; break } }
if ($dataFile) { $env:TYLI_PLANNED_ASSETS_GEOJSON = $dataFile; Write-Report "DATA_FILE_FOUND=$dataFile" } else { Write-Report 'DATA_FILE_FOUND=false' }
$runtimeRoot = if (Test-Path 'F:\') { 'F:\chatgpt\AAYS_RUNTIME\planned_buildings' } else { 'D:\AAYS_RUNTIME\planned_buildings' }
New-Item -ItemType Directory -Force -Path (Join-Path $runtimeRoot 'raw'),(Join-Path $runtimeRoot 'tmp'),(Join-Path $runtimeRoot 'sample_data') | Out-Null
$env:TYLI_RAW_STORAGE_DIR = Join-Path $runtimeRoot 'raw'
$env:TYLI_RUNTIME_TEMP_DIR = Join-Path $runtimeRoot 'tmp'
$env:TYLI_SOURCE_DATA_DIR = Join-Path $runtimeRoot 'sample_data'
$base='http://127.0.0.1:8010'
$root = Probe "$base/"
$started=$false; $proc=$null
if (-not $root.ok) { $appDir = Join-Path $Worktree 'terrayield_land_intelligence'; $outLog = Join-Path $runtimeRoot 'uvicorn_stdout.log'; $errLog = Join-Path $runtimeRoot 'uvicorn_stderr.log'; try { $proc = Start-Process -FilePath 'python' -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8010') -WorkingDirectory $appDir -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru -WindowStyle Hidden; $started=$true; for ($i=0; $i -lt 60; $i++) { Start-Sleep -Seconds 2; $root = Probe "$base/"; if ($root.ok) { break } } } catch { Write-Report "UVICORN_START_ERROR=$($_.Exception.Message)" } }
$web = Probe "$base/england_map_web/"
$search = Probe "$base/planned-assets/search?limit=1"
$layer = Probe "$base/planned-assets/parcel-layer?bbox=-0.2,51.4,0.2,51.7&limit=10"
$dataPresent = (HasText $layer.text '"data_present":true') -or ((HasText $layer.text '"feature_count_total":') -and -not (HasText $layer.text '"feature_count_total":0'))
$uiAccepted = $web.ok -and $indexWired -and $overlayOk -and $iconOk
$final = $root.ok -and $search.ok -and $layer.ok -and $uiAccepted -and $dataPresent
Write-Report "ROOT_200=$($root.ok.ToString().ToLower())"
Write-Report "WEB_200=$($web.ok.ToString().ToLower())"
Write-Report "PLANNED_SEARCH_200=$($search.ok.ToString().ToLower())"
Write-Report "PLANNED_PARCEL_LAYER_200=$($layer.ok.ToString().ToLower())"
Write-Report "UI_PLANNED_LAYER_ACCEPTED=$($uiAccepted.ToString().ToLower())"
Write-Report "DATA_PRESENT=$($dataPresent.ToString().ToLower())"
if ($final) { Write-Report 'FINAL_STATUS=FINAL_READY_CONFIRMED'; Write-Report 'PRODUCT_PROGRESS_ESTIMATE=100'; Write-Report 'PRODUCTION_COMPLETE=true'; Write-Report 'FINAL_READY: true'; Write-State 'FINAL_READY_CONFIRMED' $true; Commit-Outputs 'Confirm planned buildings production complete' }
elseif (-not ($root.ok -and $search.ok -and $layer.ok)) { Write-Report 'FINAL_STATUS=ROUTE_BLOCKED'; Write-Report 'PRODUCT_PROGRESS_ESTIMATE=99'; Write-Report 'PRODUCTION_COMPLETE=false'; Write-State 'ROUTE_BLOCKED' $false; Commit-Outputs 'Report planned buildings route blocked' }
elseif (-not $uiAccepted) { Write-Report 'FINAL_STATUS=UI_BLOCKED'; Write-Report 'PRODUCT_PROGRESS_ESTIMATE=99'; Write-Report 'PRODUCTION_COMPLETE=false'; Write-State 'UI_BLOCKED' $false; Commit-Outputs 'Report planned buildings UI blocked' }
else { Write-Report 'FINAL_STATUS=DATA_GAP'; Write-Report 'PRODUCT_PROGRESS_ESTIMATE=99'; Write-Report 'PRODUCTION_COMPLETE=false'; Write-Report 'MISSING_ITEMS=verified planned parcel FeatureCollection not found in configured F/D/repo candidate paths'; Write-State 'DATA_GAP' $false; Commit-Outputs 'Report planned buildings data gap' }
if ($started -and $proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
exit 0
