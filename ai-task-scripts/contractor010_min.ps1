$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Out=Join-Path $Bridge 'ai-results'
$Hb=Join-Path $Bridge 'ai-heartbeat\contractor010_min.md'
New-Item -ItemType Directory -Force -Path $Out,(Split-Path $Hb -Parent) | Out-Null
@('# contractor010_min','stage=start','progress=5') | Set-Content -Encoding UTF8 $Hb
Start-Sleep -Seconds 900
$Report=Join-Path $Out 'contractor010_min.report.md'
@('# contractor010_min','status=completed','PLAN_PROGRESS_PERCENT=61','TASK_COMPLETION=100/100') | Set-Content -Encoding UTF8 $Report
$Result=Join-Path $Out 'contractor010_min.result.json'
@{task_id='contractor010_min';status='finished';plan_progress_percent=61;report=$Report} | ConvertTo-Json | Set-Content -Encoding UTF8 $Result
@('# contractor010_min','stage=done','progress=100') | Set-Content -Encoding UTF8 $Hb
exit 0
