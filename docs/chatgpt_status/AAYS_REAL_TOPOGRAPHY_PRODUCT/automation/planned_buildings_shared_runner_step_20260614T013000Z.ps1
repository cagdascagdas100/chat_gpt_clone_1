$ErrorActionPreference = 'Stop'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Root = "docs/chatgpt_status/$PageKey"
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportDir = Join-Path $Root 'reports'
$StatusDir = Join-Path $Root 'status'
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir | Out-Null
$Report = Join-Path $ReportDir "planned_buildings_shared_runner_step_$ts.txt"
$Status = Join-Path $StatusDir 'planned_buildings_shared_runner_step_latest.txt'
"PAGE_KEY=$PageKey" | Out-File $Report -Encoding UTF8
"TASK=planned_buildings_shared_runner_step" | Out-File $Report -Append -Encoding UTF8
"TIMESTAMP=$(Get-Date -Format o)" | Out-File $Report -Append -Encoding UTF8
"AUTOMATION_SCRIPT=docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/planned_buildings_shared_runner_step_20260614T013000Z.ps1" | Out-File $Report -Append -Encoding UTF8
"CHECKS=control,queue,current-task,runner_tasks,automation,reports,status,heartbeat" | Out-File $Report -Append -Encoding UTF8
"NEXT=inspect shared runner contract, then queue non-conflicting planned buildings subtasks" | Out-File $Report -Append -Encoding UTF8
"FINAL_READY=false" | Out-File $Report -Append -Encoding UTF8
"COMPLETION=72" | Out-File $Report -Append -Encoding UTF8
Get-ChildItem $Root -Recurse -File -ErrorAction SilentlyContinue | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Out-File $Report -Append -Encoding UTF8
"LATEST_REPORT=$Report" | Out-File $Status -Encoding UTF8
"FINAL_READY=false" | Out-File $Status -Append -Encoding UTF8
"COMPLETION=72" | Out-File $Status -Append -Encoding UTF8
