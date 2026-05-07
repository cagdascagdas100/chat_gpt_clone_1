$ErrorActionPreference='Continue'
$TaskId='terrayield-114-runner-probe-plan-l-minipack'
$Run=Get-Date -Format 'yyyyMMdd_HHmmss'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$PlanBase='D:\6 color parcells\plan_l_run01'
$ResultDir=Join-Path $Bridge 'ai-results'
$BeatDir=Join-Path $Bridge 'ai-heartbeat'
$RunDir=Join-Path $Bridge ('.aays_runs\'+$TaskId+'_'+$Run)
New-Item -ItemType Directory -Force -Path $ResultDir,$BeatDir,$RunDir | Out-Null
$Summary=Join-Path $ResultDir ($TaskId+'-summary.md')
$Status=Join-Path $ResultDir ($TaskId+'-status.txt')
function L($x){Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
@('# Heartbeat','TASK_ID='+$TaskId,'STATUS=started','UPDATED='+(Get-Date -Format s)) | Set-Content -Encoding UTF8 (Join-Path $BeatDir ($TaskId+'.md'))
L '# TerraYield 114 runner probe and Plan L minipack'
L ('RUN='+$Run)
L ('BRIDGE_EXISTS='+(Test-Path $Bridge))
L ('PLAN_BASE_EXISTS='+(Test-Path $PlanBase))
$paths=@(
  (Join-Path $Bridge 'ai-tasks\current-task.json'),
  (Join-Path $Bridge 'ai-task-scripts'),
  (Join-Path $Bridge 'ai-results'),
  (Join-Path $PlanBase 'input\london_parcels_geometry.geojson'),
  (Join-Path $PlanBase 'input\market_3110.csv'),
  (Join-Path $PlanBase 'input\voa_london.csv'),
  (Join-Path $PlanBase 'scripts\build_london_6color.py'),
  (Join-Path $PlanBase 'output\london_6color.csv'),
  (Join-Path $PlanBase 'output\london_6color.geojson'),
  (Join-Path $PlanBase 'output\london_6color_summary.csv'),
  (Join-Path $PlanBase 'output\london_6color_confidence_summary.csv')
)
foreach($p in $paths){if(Test-Path $p){L ((Split-Path $p -Leaf)+'=exists bytes='+(Get-Item $p).Length)}else{L ((Split-Path $p -Leaf)+'=missing')}}
$py=$null
foreach($c in @('python','py')){$cmd=Get-Command $c -ErrorAction SilentlyContinue; if($cmd){$py=$cmd.Source; break}}
L ('PYTHON='+$(if($py){$py}else{'not_found'}))
$script=Join-Path $PlanBase 'scripts\build_london_6color.py'
$runExit=999
$runLog=Join-Path $RunDir 'plan_l_probe_run.log'
if($py -and (Test-Path $script)){
  try{
    if($py.ToLower().EndsWith('py.exe')){& $py -3 $script 2>&1 | Tee-Object -FilePath $runLog}else{& $py $script 2>&1 | Tee-Object -FilePath $runLog}
    $runExit=$LASTEXITCODE
  }catch{$runExit=998; ('EXCEPTION='+$_.Exception.Message)|Add-Content -Encoding UTF8 $runLog}
}else{'not runnable'|Set-Content -Encoding UTF8 $runLog}
L ('PLAN_L_RUN_EXIT='+$runExit)
function CountRows($p){try{if(Test-Path $p){return @((Import-Csv -LiteralPath $p)).Count}}catch{return -1}; return 0}
$csv=Join-Path $PlanBase 'output\london_6color.csv'
$summaryCsv=Join-Path $PlanBase 'output\london_6color_summary.csv'
$confCsv=Join-Path $PlanBase 'output\london_6color_confidence_summary.csv'
L ('CLASSIFIED_ROWS='+(CountRows $csv))
if(Test-Path $summaryCsv){L 'CLASS_SUMMARY_BEGIN'; Get-Content -Encoding UTF8 $summaryCsv | ForEach-Object {L $_}; L 'CLASS_SUMMARY_END'}
if(Test-Path $confCsv){L 'CONFIDENCE_SUMMARY_BEGIN'; Get-Content -Encoding UTF8 $confCsv | ForEach-Object {L $_}; L 'CONFIDENCE_SUMMARY_END'}
$result=if((Test-Path $csv) -and (CountRows $csv) -gt 0){'runner_alive_plan_l_outputs_present'}else{'runner_alive_but_plan_l_outputs_missing'}
@('TASK='+$TaskId,'RESULT='+$result,'PLAN_L_RUN_EXIT='+$runExit,'CLASSIFIED_ROWS='+(CountRows $csv),'RUN_DIR='+$RunDir,'NEXT_COMMAND=devam et') | Set-Content -Encoding UTF8 $Status
@('# Heartbeat','TASK_ID='+$TaskId,'STATUS=finished','UPDATED='+(Get-Date -Format s)) | Set-Content -Encoding UTF8 (Join-Path $BeatDir ($TaskId+'.md'))
exit 0
