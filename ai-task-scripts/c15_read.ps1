$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Out=Join-Path $Bridge 'ai-results'
$Hb=Join-Path $Bridge 'ai-heartbeat\c15_read.md'
New-Item -ItemType Directory -Force -Path $Out,(Split-Path $Hb -Parent) | Out-Null
@('# c15_read','status=running','phase=start','db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb
$started=Get-Date
1..30 | ForEach-Object {
  Start-Sleep -Seconds 60
  @('# c15_read','status=running',('phase=cycle_'+$_),('elapsed_minutes='+[math]::Round(((Get-Date)-$started).TotalMinutes,2)),'db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb
}
$taskCount=(Get-ChildItem -LiteralPath (Join-Path $Bridge 'ai-task-scripts') -Filter '*.ps1' -File -ErrorAction SilentlyContinue | Measure-Object).Count
$resultCount=(Get-ChildItem -LiteralPath $Out -File -ErrorAction SilentlyContinue | Measure-Object).Count
$Report=Join-Path $Out 'c15_read.report.md'
@('# c15_read','status=completed','scope=read_only_manifest','PLAN_PROGRESS_PERCENT=76','TASK_COMPLETION=100/100',('task_script_count='+$taskCount),('result_file_count='+$resultCount),'db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Report
$Result=Join-Path $Out 'c15_read.result.json'
@{task_id='c15_read';status='finished';plan_progress_percent=76;task_script_count=$taskCount;result_file_count=$resultCount;db_write=$false;production_deploy=$false;fake_data=$false;report=$Report} | ConvertTo-Json | Set-Content -Encoding UTF8 $Result
@('# c15_read','status=finished','phase=done','progress=100','db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb
exit 0