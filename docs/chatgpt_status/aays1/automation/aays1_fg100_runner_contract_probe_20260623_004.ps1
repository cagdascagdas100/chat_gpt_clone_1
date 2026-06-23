$ErrorActionPreference='Continue'
$TaskId='aays1_fg100_runner_contract_probe_20260623_004'
$PageKey='aays1'
$RepoRoot=(Resolve-Path '.').Path
$Base=Join-Path $RepoRoot "docs/chatgpt_status/$PageKey"
$Reports=Join-Path $Base 'reports'
$StatusDir=Join-Path $Base 'status'
$Heartbeat=Join-Path $Base 'heartbeat'
New-Item -ItemType Directory -Force -Path $Reports,$StatusDir,$Heartbeat | Out-Null
$Report=Join-Path $Reports ($TaskId+'_report.txt')
$Status=Join-Path $StatusDir ($TaskId+'_status.json')
$Probe=Join-Path $Reports ($TaskId+'_runner_contract_probe.txt')
$must=@('docs/chatgpt_status/aays1/control/current_task.txt','docs/chatgpt_status/aays1/queue/aays1_fg100_contract_recovery_20260623_003.queue.txt','docs/chatgpt_status/aays1/automation/aays1_fg100_contract_recovery_20260623_003.ps1')
$lines=@("TASK_ID=$TaskId","REPO_ROOT=$RepoRoot")
foreach($m in $must){ $lines += "$m exists=$(Test-Path (Join-Path $RepoRoot $m))" }
Set-Content -LiteralPath $Probe -Encoding UTF8 -Value ($lines -join "`n")
$candidates=@('C:\Users\cagda\Documents\GitHub\AAYS','C:\Users\cagda\Documents\GitHub\chat_gpt_clone_1','F:\chatgpt\AAYS','F:\chatgpt\AAYS_WORK\AAYS')
$root=''
foreach($c in $candidates){ if((Test-Path (Join-Path $c 'england_map_web/app.js')) -and (Test-Path (Join-Path $c 'terrayield_land_intelligence/app/api/routes/future_growth.py'))){ $root=$c; break } }
$api='NOT_CHECKED'
try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 8 -Uri 'http://127.0.0.1:8010/api/future-growth/layer?limit=1'; $api=[string]$r.StatusCode } catch { $api='ERROR' }
$progress=82
$state='RUNNER_PROBE_EXECUTED_NOT_FINAL'
if($root -ne ''){ $progress=85; $state='RUNNER_PROBE_FOUND_PRODUCT_ROOT_NOT_FINAL' }
if($api -eq '200'){ $progress=88; $state='RUNNER_PROBE_API_RESPONDED_NOT_FINAL' }
Set-Content -LiteralPath $Report -Encoding UTF8 -Value "STATUS=$state`nTASK_ID=$TaskId`nPAGE_KEY=$PageKey`nPROGRESS_PERCENT=$progress`nPRODUCT_ROOT=$root`nAPI_STATUS=$api`nFINAL_READY_CONFIRMED=false`nPRODUCTION_COMPLETE=false`nPOWERSHELL_REQUIRED_FROM_USER=false`nNEXT=consume_003_patch_task_or_fix_runner_pointer`n"
Set-Content -LiteralPath $Status -Encoding UTF8 -Value "{`n  \"task_id\": \"$TaskId\",`n  \"status\": \"$state\",`n  \"progress_percent\": $progress,`n  \"final_ready_confirmed\": false,`n  \"production_complete\": false,`n  \"powershell_required_from_user\": false`n}`n"
Set-Content -LiteralPath (Join-Path $Heartbeat ($TaskId+'_heartbeat.txt')) -Encoding UTF8 -Value "TASK_ID=$TaskId`nSTATUS=$state`n"
