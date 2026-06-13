$ErrorActionPreference = "Continue"
$PageKey = "AAYS_REAL_TOPOGRAPHY_PRODUCT"
$Branch = "aays-runner-v17-icon-work-20260603-232706"
$Root = "docs/chatgpt_status/$PageKey"
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"

$ReportDir = Join-Path $Root "reports"
$StatusDir = Join-Path $Root "status"
$HeartbeatDir = Join-Path $Root "heartbeat"
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir,$HeartbeatDir | Out-Null

$InventoryReport = Join-Path $ReportDir "planned_buildings_shared_runner_inventory_$Ts.txt"
$StatusReport = Join-Path $StatusDir "planned_buildings_shared_runner_status_latest.txt"
$Heartbeat = Join-Path $HeartbeatDir "planned_buildings_shared_runner_heartbeat_$Ts.txt"

"PLANNED BUILDINGS SHARED RUNNER INVENTORY" | Out-File $InventoryReport -Encoding UTF8
"PAGE_KEY=$PageKey" | Out-File $InventoryReport -Append -Encoding UTF8
"BRANCH=$Branch" | Out-File $InventoryReport -Append -Encoding UTF8
"TIMESTAMP=$(Get-Date -Format o)" | Out-File $InventoryReport -Append -Encoding UTF8
"PWD=$(Get-Location)" | Out-File $InventoryReport -Append -Encoding UTF8

foreach($d in @("control","queue","current-task","runner_tasks","automation","reports","status","heartbeat")){
  $p = Join-Path $Root $d
  "`n===== PAGE DIR: $p =====" | Out-File $InventoryReport -Append -Encoding UTF8
  if(Test-Path $p){
    Get-ChildItem $p -Force |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 80 Mode,Length,LastWriteTime,Name |
      Format-Table -AutoSize |
      Out-String |
      Out-File $InventoryReport -Append -Encoding UTF8
  } else {
    "MISSING" | Out-File $InventoryReport -Append -Encoding UTF8
  }
}

"`n===== PRODUCT TREE CHECKS =====" | Out-File $InventoryReport -Append -Encoding UTF8
$Targets = @(
  "england_map_web/app.js",
  "terrayield_land_intelligence/app/main.py",
  "terrayield_land_intelligence/app/api/routes/planned_assets.py",
  "terrayield_land_intelligence/app/services/planned_asset_service.py",
  "terrayield_land_intelligence/app/services/planned_asset_scoring.py",
  "terrayield_land_intelligence/app/schemas/planned_asset.py",
  "terrayield_land_intelligence/tests/test_planned_asset_api.py",
  "terrayield_land_intelligence/tests/test_planned_asset_data_quality.py",
  "terrayield_land_intelligence/tests/test_planned_asset_scoring.py"
)
foreach($t in $Targets){
  if(Test-Path $t){ "FOUND $t" } else { "MISSING $t" } | Out-File $InventoryReport -Append -Encoding UTF8
}

"`n===== PLANNED ENDPOINT / UI SEARCH =====" | Out-File $InventoryReport -Append -Encoding UTF8
if(Test-Path "england_map_web/app.js"){
  Select-String -Path "england_map_web/app.js" -Pattern "planned-assets|planned_buildings|planed_buildings|Nearby Planned|Planned" -CaseSensitive:$false -ErrorAction SilentlyContinue |
    Select-Object -First 80 |
    ForEach-Object { "$($_.Path):$($_.LineNumber): $($_.Line.Trim())" } |
    Out-File $InventoryReport -Append -Encoding UTF8
}

"`n===== NON-CONFLICT PLAN =====" | Out-File $InventoryReport -Append -Encoding UTF8
"READ_ONLY_INVENTORY_DONE=true" | Out-File $InventoryReport -Append -Encoding UTF8
"NO_DB_WRITE=true" | Out-File $InventoryReport -Append -Encoding UTF8
"NO_OTHER_PAGE_KEY=true" | Out-File $InventoryReport -Append -Encoding UTF8
"NEXT_REQUIRED=write product patch task after ChatGPT reads this inventory" | Out-File $InventoryReport -Append -Encoding UTF8

"SINGLE_SHARED_RUNNER_TASK_DONE=true" | Out-File $StatusReport -Encoding UTF8
"PAGE_KEY=$PageKey" | Out-File $StatusReport -Append -Encoding UTF8
"AUTOMATION_SCRIPT=docs/chatgpt_status/$PageKey/automation/planned_buildings_shared_runner_inventory_20260614T000000Z.ps1" | Out-File $StatusReport -Append -Encoding UTF8
"INVENTORY_REPORT=$InventoryReport" | Out-File $StatusReport -Append -Encoding UTF8
"FINAL_READY=false" | Out-File $StatusReport -Append -Encoding UTF8
"COMPLETION_HINT_PERCENT=70" | Out-File $StatusReport -Append -Encoding UTF8

"ALIVE $PageKey $(Get-Date -Format o)" | Out-File $Heartbeat -Encoding UTF8
