$ErrorActionPreference = "Stop"
$PageKey = "AAYS_REAL_TOPOGRAPHY_PRODUCT"
$Branch = "aays-runner-v17-icon-work-20260603-232706"
$Root = "docs/chatgpt_status/$PageKey"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"

$ReportDir = Join-Path $Root "reports"
$StatusDir = Join-Path $Root "status"
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir | Out-Null

$Out = Join-Path $ReportDir "planned_buildings_shared_runner_contract_inventory_$ts.txt"
$StatusOut = Join-Path $StatusDir "planned_buildings_shared_runner_contract_inventory_latest.txt"

"PLANNED BUILDINGS SHARED RUNNER CONTRACT INVENTORY" | Out-File $Out -Encoding UTF8
"PAGE_KEY=$PageKey" | Out-File $Out -Append -Encoding UTF8
"BRANCH=$Branch" | Out-File $Out -Append -Encoding UTF8
"TIMESTAMP=$(Get-Date -Format o)" | Out-File $Out -Append -Encoding UTF8
"PWD=$(Get-Location)" | Out-File $Out -Append -Encoding UTF8
"HEAD=$(git rev-parse HEAD)" | Out-File $Out -Append -Encoding UTF8
"" | Out-File $Out -Append -Encoding UTF8

foreach($d in @("control","queue","current-task","runner_tasks","automation","reports","status","heartbeat")){
  $p = Join-Path $Root $d
  "===== DIR: $p =====" | Out-File $Out -Append -Encoding UTF8
  if(Test-Path $p){
    Get-ChildItem $p -Force |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 120 Mode,Length,LastWriteTime,Name |
      Format-Table -AutoSize |
      Out-String |
      Out-File $Out -Append -Encoding UTF8

    Get-ChildItem $p -File -Force |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 30 |
      ForEach-Object {
        "`n----- FILE HEAD: $($_.FullName) -----" | Out-File $Out -Append -Encoding UTF8
        Get-Content $_.FullName -TotalCount 180 -ErrorAction SilentlyContinue |
          Out-File $Out -Append -Encoding UTF8
      }
  } else {
    "MISSING" | Out-File $Out -Append -Encoding UTF8
  }
  "" | Out-File $Out -Append -Encoding UTF8
}

"===== PLANNED BUILDINGS PRODUCT TARGETS =====" | Out-File $Out -Append -Encoding UTF8
$targets = @(
  "england_map_web/app.js",
  "england_map_web/index.html",
  "terrayield_land_intelligence/app/api/routes/planned_assets.py",
  "terrayield_land_intelligence/app/services/planned_asset_service.py",
  "terrayield_land_intelligence/app/services/planned_asset_scoring.py",
  "terrayield_land_intelligence/app/schemas/planned_asset.py",
  "terrayield_land_intelligence/tests/test_planned_asset_api.py",
  "terrayield_land_intelligence/tests/test_planned_asset_data_quality.py"
)
foreach($t in $targets){
  if(Test-Path $t){
    "FOUND: $t" | Out-File $Out -Append -Encoding UTF8
  } else {
    "MISSING: $t" | Out-File $Out -Append -Encoding UTF8
  }
}

"===== RUNNER / QUEUE / BRIDGE CANDIDATES =====" | Out-File $Out -Append -Encoding UTF8
Get-ChildItem . -Recurse -File -Force -ErrorAction SilentlyContinue |
  Where-Object {
    $_.FullName -match "runner|queue|current-task|current_task|poller|bridge|heartbeat|runner_tasks|automation" -and
    $_.FullName -notmatch "\\.git\\" -and
    $_.Length -lt 2MB
  } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 300 FullName,Length,LastWriteTime |
  Format-Table -AutoSize |
  Out-String |
  Out-File $Out -Append -Encoding UTF8

"STATUS=CONTRACT_INVENTORY_WRITTEN" | Out-File $StatusOut -Encoding UTF8
"PAGE_KEY=$PageKey" | Out-File $StatusOut -Append -Encoding UTF8
"SCRIPT=docs/chatgpt_status/$PageKey/automation/planned_buildings_shared_runner_contract_inventory_20260614T120000Z.ps1" | Out-File $StatusOut -Append -Encoding UTF8
"OUTPUT_REPORT=$Out" | Out-File $StatusOut -Append -Encoding UTF8
"FINAL_READY=false" | Out-File $StatusOut -Append -Encoding UTF8
"TIMESTAMP=$(Get-Date -Format o)" | Out-File $StatusOut -Append -Encoding UTF8

try {
  git add $Out $StatusOut
  git commit -m "Add planned buildings shared runner inventory report"
  git push origin HEAD:$Branch
} catch {
  $_ | Out-File (Join-Path $ReportDir "planned_buildings_shared_runner_inventory_push_error_$ts.txt") -Encoding UTF8
  throw
}
