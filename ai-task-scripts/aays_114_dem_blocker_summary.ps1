$TaskId='aays-114-dem-blocker-summary'
$Root=Split-Path -Parent $PSScriptRoot
$OutDir=Join-Path $Root 'ai-results'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutDir,$HbDir|Out-Null
$Out=Join-Path $OutDir ($TaskId+'.result.json')
$Md=Join-Path $OutDir ($TaskId+'.report.md')
$Hb=Join-Path $HbDir 'portable-runner.md'
Set-Content -Path $Hb -Encoding UTF8 -Value @('# runner','Status: running',('TaskId: '+$TaskId))
$result=[ordered]@{task_id=$TaskId;status='complete';blocker='no local DEM or DTM raster candidate found';next_step='place DEM or DTM raster under E:/AAYS_DATA/topography or E:/AAYS_DATA/terrain then rerun AAYS 112';db_write=$false;production_deploy=$false}
$result|ConvertTo-Json -Depth 4|Set-Content -Path $Out -Encoding UTF8
@('# AAYS 114 DEM Blocker Summary','',('Blocker: '+$result.blocker),('Next: '+$result.next_step),'TASK_COMPLETION=100/100')|Set-Content -Path $Md -Encoding UTF8
Set-Content -Path $Hb -Encoding UTF8 -Value @('# runner','Status: finished',('TaskId: '+$TaskId))
Write-Output ($result|ConvertTo-Json -Depth 4)
exit 0
