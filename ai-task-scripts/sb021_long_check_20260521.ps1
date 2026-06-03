$Root=Split-Path -Parent $PSScriptRoot
$TaskId='sb021-long-check-20260521'
$Res=Join-Path $Root 'ai-results'
$Prog=Join-Path $Root 'ai-progress'
New-Item -ItemType Directory -Force -Path $Res,$Prog | Out-Null
$P=Join-Path $Prog ($TaskId+'.progress.md')
$R=Join-Path $Res ($TaskId+'.result.json')
$M=Join-Path $Res ($TaskId+'.report.md')
Set-Content -Encoding UTF8 -Path $M -Value '# sb021 long check'
$items=@('docs/chatgpt_status/multi_page_status.json','ai-tasks/current-task.json','ai-tasks/.last-task-id','ai-heartbeat/portable-runner.md','ai-results')
$seen=@()
for($i=1;$i -le 12;$i++){
  @('# sb021','cycle: '+$i,'percent: '+[int]($i*100/12)) | Set-Content -Encoding UTF8 -Path $P
  Add-Content -Encoding UTF8 -Path $M -Value ('## cycle '+$i)
  foreach($x in $items){
    $f=Join-Path $Root $x
    $line=$x+' exists='+(Test-Path -LiteralPath $f)
    Add-Content -Encoding UTF8 -Path $M -Value $line
    $seen+=$line
  }
  if($i -lt 12){ Start-Sleep -Seconds 180 }
}
@{task_id=$TaskId;status='completed';seen=$seen;db_write=$false;production_deploy=$false}|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 -Path $R
Write-Host 'SB021_DONE'
exit 0