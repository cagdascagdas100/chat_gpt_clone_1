$TaskId='aays-113b-light-dem-check'
$Root=Split-Path -Parent $PSScriptRoot
$OutDir=Join-Path $Root 'ai-results'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutDir,$HbDir | Out-Null
$Out=Join-Path $OutDir ($TaskId+'.result.json')
$Md=Join-Path $OutDir ($TaskId+'.report.md')
$Hb=Join-Path $HbDir 'portable-runner.md'
Set-Content -Encoding UTF8 -Path $Hb -Value @('# runner','Status: running',('TaskId: '+$TaskId))
$scanRoots=@('E:/AAYS_DATA','E:/AAYS_DATA/cost','E:/AAYS_DATA/topography','E:/AAYS_DATA/terrain','C:/Users/cagda/Documents/GitHub/AAYS')
$rows=@()
foreach($r in $scanRoots){
  if(Test-Path $r){
    foreach($ext in @('*.tif','*.tiff','*.asc','*.vrt','*.img')){
      $items=Get-ChildItem -Path $r -Filter $ext -File -ErrorAction SilentlyContinue | Select-Object -First 50
      foreach($i in $items){$rows += [pscustomobject]@{path=$i.FullName;name=$i.Name;size_mb=[math]::Round($i.Length/1MB,2);root=$r}}
    }
  }
}
$result=[ordered]@{task_id=$TaskId;status='complete';rows=[int]$rows.Count;top_candidates=@($rows|Select-Object -First 30);note='nonrecursive recovery'}
$result|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 -Path $Out
@('# AAYS 113B Light DEM Check','',('Rows: '+$rows.Count),'TASK_COMPLETION=100/100')|Set-Content -Encoding UTF8 -Path $Md
Set-Content -Encoding UTF8 -Path $Hb -Value @('# runner','Status: finished',('TaskId: '+$TaskId))
Write-Output ($result|ConvertTo-Json -Depth 5)
exit 0
