$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Estate='E:\AAYS_DATA\estate_agents'
$Out=Join-Path $Bridge 'ai-results'
$Hb=Join-Path $Bridge 'ai-heartbeat\portable-runner.md'
$TaskId='real100-check-20260524-r1'
New-Item -ItemType Directory -Force -Path $Estate,$Out,(Split-Path $Hb -Parent) | Out-Null
$Start=Get-Date -Format s
@('# AAYS Portable Task Runner Fixed','','Time: '+$Start,'Status: running','TaskId: '+$TaskId,'TaskFile: '+(Join-Path $Bridge 'ai-tasks\current-task.json'),'Message: real check running','Mode: single-runner-parallel-check','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 $Hb
$jobs=@()
$jobs += Start-Job -Name inv -ScriptBlock { param($Estate) Get-ChildItem -Path $Estate -File -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime | ConvertTo-Csv -NoTypeInformation | Set-Content -Encoding UTF8 (Join-Path $Estate 'estate_existing_artifact_inventory_002.csv') } -ArgumentList $Estate
$jobs += Start-Job -Name plan -ScriptBlock { param($Estate) @{status='created';source_policy='real evidence only';fake_rows='not allowed'} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Estate 'estate_agent_source_acquisition_plan_002.json') } -ArgumentList $Estate
$jobs += Start-Job -Name rules -ScriptBlock { param($Estate) @('# Scoring rules','Real evidence required. Missing evidence stays review mode.') | Set-Content -Encoding UTF8 (Join-Path $Estate 'estate_agent_coverage_scoring_rules_002.md') } -ArgumentList $Estate
$jobs += Start-Job -Name candidates -ScriptBlock { param($Estate,$Out) $p=Join-Path $Estate 'estate_agent_candidates_from_local_artifacts_003.csv'; $o=@{exists=Test-Path $p; rows=0}; if(Test-Path $p){$o.rows=[Math]::Max(0,(Get-Content $p).Count-1)}; $o | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Out 'real100_candidates.json') } -ArgumentList $Estate,$Out
Wait-Job -Job $jobs -Timeout 600 | Out-Null
$jobs | Remove-Job -Force -ErrorAction SilentlyContinue
$req=@('estate_agent_source_acquisition_plan_002.json','estate_agent_coverage_scoring_rules_002.md','estate_existing_artifact_inventory_002.csv','estate_agent_candidates_from_local_artifacts_003.csv','estate_agent_verified_export_dryrun_006.csv')
$r=@(); foreach($n in $req){$p=Join-Path $Estate $n; $r += @{file=$n; exists=Test-Path $p; bytes=if(Test-Path $p){(Get-Item $p).Length}else{0}}}
$r | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Out 'real100_check_20260524.result.json')
@('# Real 100 Check','status=finished','review_required=true','db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 (Join-Path $Out 'real100_check_20260524.report.md')
$Finish=Get-Date -Format s
@('# AAYS Portable Task Runner Fixed','','Time: '+$Finish,'Status: finished','TaskId: '+$TaskId,'TaskFile: '+(Join-Path $Bridge 'ai-tasks\current-task.json'),'Message: exit=0','Mode: single-runner-parallel-check','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 $Hb
exit 0
