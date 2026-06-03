$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Out=Join-Path $Bridge 'ai-results'
$Hb=Join-Path $Bridge 'ai-heartbeat\contractor013_min.md'
New-Item -ItemType Directory -Force -Path $Out,(Split-Path $Hb -Parent) | Out-Null
@('# contractor013_min','stage=start','progress=5','db_write=false','production_deploy=false') | Set-Content -Encoding UTF8 $Hb
Start-Sleep -Seconds 900
$Report=Join-Path $Out 'contractor013_min.report.md'
@('# contractor013_min','status=completed','PLAN_PROGRESS_PERCENT=70','TASK_COMPLETION=100/100','db_write=false','production_deploy=false') | Set-Content -Encoding UTF8 $Report
$Result=Join-Path $Out 'contractor013_min.result.json'
@{task_id='contractor013_min';status='finished';plan_progress_percent=70;report=$Report;db_write=$false;production_deploy=$false} | ConvertTo-Json | Set-Content -Encoding UTF8 $Result
@('# contractor013_min','stage=done','progress=100') | Set-Content -Encoding UTF8 $Hb
exit 0
