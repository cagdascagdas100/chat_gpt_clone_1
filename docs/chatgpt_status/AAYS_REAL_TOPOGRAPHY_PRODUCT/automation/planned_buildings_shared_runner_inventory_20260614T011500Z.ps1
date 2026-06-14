$ErrorActionPreference = 'Stop'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Root = "docs/chatgpt_status/$PageKey"
$ReportDir = Join-Path $Root 'reports'
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$Out = Join-Path $ReportDir 'planned_buildings_shared_runner_inventory_20260614T011500Z.txt'
"PAGE_KEY=$PageKey" | Out-File $Out -Encoding UTF8
"TASK=planned_buildings_shared_runner_inventory_20260614T011500Z" | Out-File $Out -Append -Encoding UTF8
"TIMESTAMP=$(Get-Date -Format o)" | Out-File $Out -Append -Encoding UTF8
foreach($d in @('control','queue','current-task','runner_tasks','automation','reports','status','heartbeat')){
  $p = Join-Path $Root $d
  "`nDIR=$p" | Out-File $Out -Append -Encoding UTF8
  if(Test-Path $p){
    Get-ChildItem $p -Force | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Out-File $Out -Append -Encoding UTF8
  } else {
    'MISSING' | Out-File $Out -Append -Encoding UTF8
  }
}
