$ErrorActionPreference='Continue'
$TaskId='terrayield-113-plan-l-accuracy-lite'
$Run=Get-Date -Format 'yyyyMMdd_HHmmss'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$PlanBase='D:\6 color parcells\plan_l_run01'
$ScriptDir=Join-Path $PlanBase 'scripts'
$OutputDir=Join-Path $PlanBase 'output'
$QaDir=Join-Path $OutputDir 'qa'
$ResultDir=Join-Path $Bridge 'ai-results'
$BeatDir=Join-Path $Bridge 'ai-heartbeat'
$RunDir=Join-Path $Bridge ('.aays_runs\'+$TaskId+'_'+$Run)
New-Item -ItemType Directory -Force -Path $ScriptDir,$QaDir,$ResultDir,$BeatDir,$RunDir | Out-Null
$Summary=Join-Path $ResultDir ($TaskId+'-summary.md')
$Status=Join-Path $ResultDir ($TaskId+'-status.txt')
function AddLine($x){Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
@('# Heartbeat','TASK_ID='+$TaskId,'STATUS=starting','UPDATED='+(Get-Date -Format s)) | Set-Content -Encoding UTF8 (Join-Path $BeatDir ($TaskId+'.md'))
AddLine '# Plan L accuracy lite task'
$src=Join-Path $Bridge 'ai-task-scripts\plan_l_accuracy_expander.py'
$dst=Join-Path $ScriptDir 'plan_l_accuracy_expander.py'
if(Test-Path $src){Copy-Item -Force $src $dst}
$py=$null
foreach($c in @('python','py')){$cmd=Get-Command $c -ErrorAction SilentlyContinue; if($cmd){$py=$cmd.Source; break}}
$log=Join-Path $RunDir 'accuracy_lite.log'
$exit=999
if($py -and (Test-Path $dst)){
  try{
    if($py.ToLower().EndsWith('py.exe')){& $py -3 $dst 2>&1 | Tee-Object -FilePath $log}else{& $py $dst 2>&1 | Tee-Object -FilePath $log}
    $exit=$LASTEXITCODE
  }catch{$exit=998; ('EXCEPTION='+$_.Exception.Message)|Add-Content -Encoding UTF8 $log}
}else{'not runnable'|Set-Content -Encoding UTF8 $log}
function Rows($p){try{if(Test-Path $p){return @((Import-Csv -LiteralPath $p)).Count}}catch{return -1}; return 0}
$conflicts=Rows (Join-Path $QaDir 'qa_conflict_candidates.csv')
$manual=Rows (Join-Path $QaDir 'qa_recommended_manual_review.csv')
$classified=Rows (Join-Path $OutputDir 'london_6color.csv')
AddLine ('PYTHON_EXIT='+$exit)
AddLine ('CLASSIFIED_ROWS='+$classified)
AddLine ('CONFLICT_CANDIDATES='+$conflicts)
AddLine ('MANUAL_REVIEW_CANDIDATES='+$manual)
if(Test-Path (Join-Path $QaDir 'PLAN_L_ACCURACY_EXPANSION_REPORT.md')){Get-Content -Encoding UTF8 (Join-Path $QaDir 'PLAN_L_ACCURACY_EXPANSION_REPORT.md') -TotalCount 120 | ForEach-Object {AddLine $_}}
$result=if($exit -eq 0){'completed_accuracy_lite'}else{'needs_attention_accuracy_lite'}
@('TASK='+$TaskId,'RESULT='+$result,'PYTHON_EXIT='+$exit,'CLASSIFIED_ROWS='+$classified,'CONFLICT_CANDIDATES='+$conflicts,'MANUAL_REVIEW_CANDIDATES='+$manual,'RUN_DIR='+$RunDir,'NEXT_COMMAND=devam et') | Set-Content -Encoding UTF8 $Status
@('# Heartbeat','TASK_ID='+$TaskId,'STATUS=finished','UPDATED='+(Get-Date -Format s)) | Set-Content -Encoding UTF8 (Join-Path $BeatDir ($TaskId+'.md'))
exit 0
