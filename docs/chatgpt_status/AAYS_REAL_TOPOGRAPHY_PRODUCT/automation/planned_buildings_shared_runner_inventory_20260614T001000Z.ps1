$ErrorActionPreference = "Continue"
$PageKey = "AAYS_REAL_TOPOGRAPHY_PRODUCT"
$Root = "docs/chatgpt_status/$PageKey"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir = Join-Path $Root "reports"
$StatusDir = Join-Path $Root "status"
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir | Out-Null
$Report = Join-Path $ReportDir "planned_buildings_shared_runner_inventory_$Timestamp.txt"
$Status = Join-Path $StatusDir "planned_buildings_shared_runner_inventory_latest.txt"
"PLANNED BUILDINGS SHARED RUNNER INVENTORY" | Out-File $Report -Encoding UTF8
"PAGE_KEY=$PageKey" | Out-File $Report -Append -Encoding UTF8
"TIMESTAMP=$(Get-Date -Format o)" | Out-File $Report -Append -Encoding UTF8
"BRANCH=$(git branch --show-current)" | Out-File $Report -Append -Encoding UTF8
"HEAD=$(git rev-parse HEAD)" | Out-File $Report -Append -Encoding UTF8
foreach($dir in @("control","queue","current-task","runner_tasks","automation","reports","status","heartbeat")){
  $p = Join-Path $Root $dir
  "`n===== $p =====" | Out-File $Report -Append -Encoding UTF8
  if(Test-Path $p){
    Get-ChildItem $p -Force | Sort-Object LastWriteTime -Descending | Select-Object -First 120 Mode,Length,LastWriteTime,Name | Format-Table -AutoSize | Out-String | Out-File $Report -Append -Encoding UTF8
  } else {
    "MISSING" | Out-File $Report -Append -Encoding UTF8
  }
}
"`n===== NON CONFLICTING READ ONLY CHECKS =====" | Out-File $Report -Append -Encoding UTF8
$checks = @(
  "england_map_web/app.js",
  "england_map_web/app.py",
  "england_map_web/routes/planned_assets.py",
  "england_map_web/planned_assets.py",
  "tests/test_planned_assets.py",
  "tests/test_planned_buildings.py"
)
foreach($f in $checks){
  "`n--- $f ---" | Out-File $Report -Append -Encoding UTF8
  if(Test-Path $f){
    "EXISTS length=$((Get-Item $f).Length)" | Out-File $Report -Append -Encoding UTF8
    Select-String -Path $f -Pattern "planned|building|parcel|legend|probability|completion|confidence|source" -CaseSensitive:$false -ErrorAction SilentlyContinue | Select-Object -First 80 | Out-String | Out-File $Report -Append -Encoding UTF8
  } else {
    "MISSING" | Out-File $Report -Append -Encoding UTF8
  }
}
"FINAL_READY=false" | Out-File $Status -Encoding UTF8
"EXPECTED_NEXT=review planned_buildings_shared_runner_inventory report and write exact product patch task only after queue contract is confirmed" | Out-File $Status -Append -Encoding UTF8
"REPORT=$Report" | Out-File $Status -Append -Encoding UTF8
git add $Report $Status
git commit -m "Add planned buildings shared runner inventory report"