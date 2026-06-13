$ErrorActionPreference = "Stop"

$PageKey = "AAYS_REAL_TOPOGRAPHY_PRODUCT"
$Branch = "aays-runner-v17-icon-work-20260603-232706"
$Root = "docs/chatgpt_status/$PageKey"
$TaskName = "planned_buildings_shared_runner_apply_20260614T000000Z"

$RepoRoot = (Get-Location).Path
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir = Join-Path $Root "reports"
$StatusDir = Join-Path $Root "status"
$HeartbeatDir = Join-Path $Root "heartbeat"
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir,$HeartbeatDir | Out-Null

$Report = Join-Path $ReportDir "${TaskName}_report_$ts.txt"
$Status = Join-Path $StatusDir "${TaskName}_status_latest.txt"
$Heartbeat = Join-Path $HeartbeatDir "${TaskName}_heartbeat_$ts.txt"

function Write-Line([string]$s) { $s | Out-File $Report -Append -Encoding UTF8 }

"TASK=$TaskName" | Out-File $Report -Encoding UTF8
Write-Line "PAGE_KEY=$PageKey"
Write-Line "BRANCH_EXPECTED=$Branch"
Write-Line "TIMESTAMP=$(Get-Date -Format o)"
Write-Line "REPO_ROOT=$RepoRoot"
Write-Line "GIT_BRANCH=$(git branch --show-current)"
Write-Line "GIT_HEAD=$(git rev-parse HEAD)"
Write-Line ""

"ALIVE $TaskName $(Get-Date -Format o)" | Out-File $Heartbeat -Encoding UTF8

foreach($d in @("control","queue","current-task","runner_tasks","automation","reports","status","heartbeat")){
  $p = Join-Path $Root $d
  Write-Line "===== DIR: $p ====="
  if(Test-Path $p){
    Get-ChildItem $p -Force |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 80 Mode,Length,LastWriteTime,Name |
      Format-Table -AutoSize |
      Out-String |
      Out-File $Report -Append -Encoding UTF8
  } else {
    Write-Line "MISSING"
  }
}

Write-Line "===== PRODUCT TARGET PROBE ====="
$Targets = @(
  "england_map_web/app.js",
  "england_map_web/index.html",
  "terrayield_land_intelligence/app/main.py",
  "terrayield_land_intelligence/app/api/routes/planned_assets.py",
  "terrayield_land_intelligence/app/services/planned_asset_service.py",
  "terrayield_land_intelligence/app/schemas/planned_asset.py",
  "terrayield_land_intelligence/tests/test_planned_asset_api.py",
  "terrayield_land_intelligence/tests/test_planned_asset_data_quality.py",
  "terrayield_land_intelligence/docs/chatgpt_handoff/planned_buildings_parcel_layer_low_credit_20260612"
)
foreach($t in $Targets){
  if(Test-Path $t){ Write-Line "EXISTS: $t" } else { Write-Line "MISSING: $t" }
}

Write-Line "===== PLANNED BUILDINGS REFERENCES ====="
Get-ChildItem . -Recurse -File -Force -ErrorAction SilentlyContinue |
  Where-Object {
    $_.FullName -notmatch "\\.git\\" -and
    $_.Length -lt 2MB -and
    ($_.Name -match "planned|building|asset|parcel-layer|contract|inventory|task|runner|queue|automation")
  } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 300 FullName,Length,LastWriteTime |
  Format-Table -AutoSize |
  Out-String |
  Out-File $Report -Append -Encoding UTF8

$finalReady = "false"
$completion = "66"
$nextExpected = "shared_runner_product_apply_or_gap_report_planned_buildings_<timestamp>.txt"

@"
TASK=$TaskName
PAGE_KEY=$PageKey
FINAL_READY=$finalReady
COMPLETION_PERCENT=$completion
NEXT_EXPECTED_REPORT=$nextExpected
TIMESTAMP=$(Get-Date -Format o)
REPORT=$Report
"@ | Out-File $Status -Encoding UTF8

git add $Report $Status $Heartbeat
if(git status --porcelain){
  git commit -m "Run planned buildings shared runner automation"
  git push origin HEAD:$Branch
}

Write-Output "OK: $Report"
