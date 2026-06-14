$ErrorActionPreference = 'Stop'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Root = "docs/chatgpt_status/$PageKey"
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportDir = Join-Path $Root 'reports'
$StatusDir = Join-Path $Root 'status'
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir | Out-Null
$Report = Join-Path $ReportDir "planned_buildings_shared_inventory_20260614T040000Z_$Stamp.txt"
$Status = Join-Path $StatusDir 'planned_buildings_shared_inventory_latest.txt'

"PAGE_KEY=$PageKey" | Out-File $Report -Encoding UTF8
"RUN_AT=$(Get-Date -Format o)" | Out-File $Report -Append -Encoding UTF8
"TASK=planned_buildings_shared_inventory_20260614T040000Z" | Out-File $Report -Append -Encoding UTF8
"AUTOMATION_SCRIPT=docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/planned_buildings_shared_inventory_20260614T040000Z.ps1" | Out-File $Report -Append -Encoding UTF8

foreach($d in @('control','queue','current-task','runner_tasks','automation','reports','status','heartbeat')){
  $p = Join-Path $Root $d
  "`n===== $p =====" | Out-File $Report -Append -Encoding UTF8
  if(Test-Path $p){
    Get-ChildItem $p -Force | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Mode,Length,LastWriteTime,Name | Format-Table -AutoSize | Out-String | Out-File $Report -Append -Encoding UTF8
  } else {
    'MISSING' | Out-File $Report -Append -Encoding UTF8
  }
}

@"
PAGE_KEY=$PageKey
TASK=planned_buildings_shared_inventory_20260614T040000Z
REPORT=$Report
STATUS=INVENTORY_DONE
UPDATED_AT=$(Get-Date -Format o)
"@ | Out-File $Status -Encoding UTF8
