$ErrorActionPreference='Continue'
$Root='C:/AAYS_GITHUB_BRIDGE_CLEAN2'
$TaskId='terrayield-queue-guard-run-pending-20260520'
$Progress=Join-Path $Root 'ai-progress'
$Results=Join-Path $Root 'ai-results'
$Pending=Join-Path $Root 'ai-tasks/pending'
New-Item -ItemType Directory -Force -Path $Progress,$Results,$Pending | Out-Null
$ProgressPath=Join-Path $Progress ($TaskId+'.progress.md')
$ResultPath=Join-Path $Results ($TaskId+'.result.json')
$items=Get-ChildItem -Path $Pending -Filter '*.json' -File -ErrorAction SilentlyContinue
for($i=1;$i -le 8;$i++){
  @('# queue guard clean2','',"cycle: $i","pending_count: $($items.Count)","checked_at: $((Get-Date).ToString('s'))") | Set-Content -Encoding UTF8 $ProgressPath
  if($i -lt 8){ Start-Sleep -Seconds 240 }
}
@{task_id=$TaskId;status='clean2_scan_complete';pending_count=$items.Count;root=$Root;no_db_write=$true;no_production_deploy=$true}|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 $ResultPath
Write-Host 'QUEUE_GUARD_CLEAN2_DONE'
exit 0