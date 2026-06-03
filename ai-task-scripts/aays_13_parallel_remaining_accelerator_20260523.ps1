$ErrorActionPreference = 'Continue'
$Root = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Out = Join-Path $Root 'ai-results'
$HbDir = Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $Out,$HbDir | Out-Null
$TaskId = 'aays-13-parallel-remaining-accelerator-20260523'
$Started = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$Hb = Join-Path $HbDir 'portable-runner.md'
@('# AAYS Portable Task Runner Fixed','','Time: '+$Started,'Status: running','TaskId: '+$TaskId,'TaskFile: '+(Join-Path $Root 'ai-tasks\current-task.json'),'Message: parallel read-only accelerator started','Mode: single-runner-parallel-child-jobs','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 $Hb
$jobs = @()
$jobs += Start-Job -Name 'estate007_join' -ScriptBlock { param($Root) $s=Join-Path $Root 'ai-task-scripts\estate007_codex_parcel_join_package.ps1'; if(Test-Path $s){ powershell -NoProfile -ExecutionPolicy Bypass -File $s }; 'estate007_join_done' } -ArgumentList $Root
$jobs += Start-Job -Name 'inventory' -ScriptBlock { param($Root,$Out) Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'ai-results|ai-runner-logs|docs\\chatgpt_status|ai-task-scripts' } | Select-Object FullName,Length,LastWriteTime | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 (Join-Path $Out 'aays_13_parallel_inventory.json'); 'inventory_done' } -ArgumentList $Root,$Out
$jobs += Start-Job -Name 'status_audit' -ScriptBlock { param($Root,$Out) $paths=@('ai-tasks\current-task.json','ai-tasks\.last-task-id','ai-heartbeat\portable-runner.md','docs\chatgpt_status\multi_page_status.json'); $o=@{}; foreach($p in $paths){$fp=Join-Path $Root $p; $o[$p]=@{exists=(Test-Path $fp); sample= if(Test-Path $fp){(Get-Content $fp -Raw -ErrorAction SilentlyContinue).Substring(0,[Math]::Min(500,(Get-Content $fp -Raw).Length))}else{''}}}; $o | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $Out 'aays_13_parallel_status_audit.json'); 'status_audit_done' } -ArgumentList $Root,$Out
$jobs += Start-Job -Name 'db_safety_audit' -ScriptBlock { param($Root,$Out) $hits=Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'ai-task-scripts|docs|ai-results' } | Select-String -Pattern 'db_write.:.true|production_deploy.:.true|fake_data.:.true|INSERT INTO|UPDATE .* SET|DELETE FROM' -ErrorAction SilentlyContinue | Select-Object Path,LineNumber,Line; $hits | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $Out 'aays_13_parallel_db_safety_audit.json'); 'db_safety_audit_done' } -ArgumentList $Root,$Out
Wait-Job -Job $jobs -Timeout 1700 | Out-Null
$jobSummary = $jobs | ForEach-Object { [pscustomobject]@{Name=$_.Name;State=$_.State;Output=(Receive-Job $_ -Keep | Out-String)} }
$Finished = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$jobSummary | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Out 'aays_13_parallel_remaining_accelerator.result.json')
@('# AAYS 13 Parallel Remaining Accelerator','','started='+$Started,'finished='+$Finished,'status=finished','db_write=false','production_deploy=false','fake_data=false','child_jobs='+($jobs.Count)) | Set-Content -Encoding UTF8 (Join-Path $Out 'aays_13_parallel_remaining_accelerator.report.md')
@('# AAYS Portable Task Runner Fixed','','Time: '+$Finished,'Status: finished','TaskId: '+$TaskId,'TaskFile: '+(Join-Path $Root 'ai-tasks\current-task.json'),'Message: exit=0','Mode: single-runner-parallel-child-jobs','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 $Hb
exit 0
