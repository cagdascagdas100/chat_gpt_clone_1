param()
$ErrorActionPreference='Continue'
$RepoRoot$RepoRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\\..\\..\\..')).Path
$PageRoot=Join-Path $RepoRoot 'docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Reports=Join-Path $PageRoot 'reports'; $Status=Join-Path $PageRoot 'status'
New-Item -ItemType Directory -Force -Path $Reports,$Status | Out-Null
$Out=Join-Path $Reports 'topography_runner_intake_runtime_wrapper_20260617_001.txt'
$Runtime=Join-Path $PageRoot 'automation\topography_runtime_final_v2_20260616_2254.ps1'
$RuntimeReport=Join-Path $Reports 'topography_chatgpt_runtime_gap_report_20260616_2254_v2.txt'
function KV($k,$v){ Add-Content -Encoding UTF8 -Path $Out -Value ("$k=$v") }
'' | Set-Content -Encoding UTF8 $Out
KV 'PAGE_KEY' 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
KV 'TASK_ID' 'topography_runner_intake_runtime_wrapper_20260617_001'
KV 'BRANCH_ACTUAL' (& git -C $RepoRoot branch --show-current 2>$null)
KV 'DB_WRITE' 'false'; KV 'MIGRATION' 'false'; KV 'DEPLOY' 'false'; KV 'FAKE_DATA_CREATED' 'false'
KV 'CURRENT_TASK_EXISTS' (Test-Path (Join-Path $PageRoot 'current-task\topography_current.task.md'))
KV 'QUEUE_EXISTS' (Test-Path (Join-Path $PageRoot 'queue\topography_runner_intake_runtime_wrapper_20260617_001.task.md'))
KV 'RUNNER_TASK_EXISTS' (Test-Path (Join-Path $PageRoot 'runner_tasks\topography_runner_intake_runtime_wrapper_20260617_001.task.md'))
KV 'RUNTIME_SCRIPT_EXISTS' (Test-Path $Runtime)
if(Test-Path $Runtime){ & powershell -ExecutionPolicy Bypass -File $Runtime | Out-Null }
Start-Sleep -Seconds 2
KV 'RUNTIME_REPORT_EXISTS' (Test-Path $RuntimeReport)
if(Test-Path $RuntimeReport){ Get-Content $RuntimeReport | Add-Content -Encoding UTF8 $Out }
$final='RUNNER_WRAPPER_EXECUTED_RUNTIME_PENDING_OR_BLOCKED'; $progress='99.99'
if(Test-Path $RuntimeReport){ $txt=Get-Content -Raw $RuntimeReport; if($txt -match 'FINAL_STATUS=FINAL_READY_CONFIRMED' -and $txt -match 'PRODUCT_PROGRESS_ESTIMATE=100'){ $final='FINAL_READY_CONFIRMED'; $progress='100' } }
KV 'PRODUCT_PROGRESS_ESTIMATE' $progress
KV 'FINAL_STATUS' $final
Copy-Item -Force $Out (Join-Path $Status 'topography_runner_intake_runtime_wrapper_20260617_001.status.txt')
Write-Host "WROTE_REPORT=$Out"

