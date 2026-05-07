$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-111-plan-l-deep-parallel-qa'
$Run = Get-Date -Format 'yyyyMMdd_HHmmss'
$Bridge = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlanBase = 'D:\6 color parcells\plan_l_run01'
$InputDir = Join-Path $PlanBase 'input'
$OutputDir = Join-Path $PlanBase 'output'
$ScriptDir = Join-Path $PlanBase 'scripts'
$LogDirPlan = Join-Path $PlanBase 'logs'
$ResultDir = Join-Path $Bridge 'ai-results'
$BeatDir = Join-Path $Bridge 'ai-heartbeat'
$RunDir = Join-Path $Bridge ('.aays_runs\' + $TaskId + '_' + $Run)
$SlotsDir = Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $ResultDir,$BeatDir,$RunDir,$SlotsDir,$ScriptDir,$OutputDir,$LogDirPlan | Out-Null
$Summary = Join-Path $ResultDir ($TaskId + '-summary.md')
$Status = Join-Path $ResultDir ($TaskId + '-status.txt')
$Score = Join-Path $ResultDir ($TaskId + '-scorecard.csv')
function W([string]$x){ Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x }
function B([string]$s){ @('# AAYS Heartbeat','TASK_ID=' + $TaskId,'STATUS=' + $s,'UPDATED=' + (Get-Date -Format s)) | Set-Content -Encoding UTF8 (Join-Path $BeatDir ($TaskId + '.md')) }
function Slot([string]$n,[string]$r,[string[]]$lines){ @('# ' + $n,'TASK_ID=' + $TaskId,'RESULT=' + $r,'UPDATED=' + (Get-Date -Format s),'') + $lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir ($n + '.md')) }
function Rows([string]$p){ try{ if(Test-Path $p){ return @((Import-Csv -LiteralPath $p)).Count } }catch{ return -1 } return 0 }
function JsonFeatures([string]$p){ try{ if(Test-Path $p){ $j=Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json; return $j.features.Count } }catch{ return -1 } return 0 }
B 'starting'
W '# TerraYield 111 Plan L Deep Parallel QA'
W 'MODE=single_devam_deeper_parallel; rerun_classifier_if_possible; generate_deep_qa; no_external_secret_work'
W ('PLAN_BASE=' + $PlanBase)
W ('BRIDGE=' + $Bridge)

$sourceClassifier = Join-Path $Bridge 'ai-task-scripts\build_london_6color_plan_l.py'
$targetClassifier = Join-Path $ScriptDir 'build_london_6color.py'
$sourceQA = Join-Path $Bridge 'ai-task-scripts\plan_l_deep_qa.py'
$targetQA = Join-Path $ScriptDir 'plan_l_deep_qa.py'
if(Test-Path $sourceClassifier){ Copy-Item -Force $sourceClassifier $targetClassifier; Slot 'slot_01_classifier_sync' 'completed' @('synced_to=' + $targetClassifier, 'bytes=' + (Get-Item $targetClassifier).Length) } else { Slot 'slot_01_classifier_sync' 'blocked' @('missing=' + $sourceClassifier) }
if(Test-Path $sourceQA){ Copy-Item -Force $sourceQA $targetQA; Slot 'slot_02_deep_qa_sync' 'completed' @('synced_to=' + $targetQA, 'bytes=' + (Get-Item $targetQA).Length) } else { Slot 'slot_02_deep_qa_sync' 'blocked' @('missing=' + $sourceQA) }

$PythonExe = $null
foreach($c in @('python','py')){ $cmd=Get-Command $c -ErrorAction SilentlyContinue; if($cmd){ $PythonExe=$cmd.Source; break } }
Slot 'slot_03_python_discovery' $(if($PythonExe){'completed'}else{'blocked'}) @('python_exe=' + $(if($PythonExe){$PythonExe}else{'not_found'}))

B 'running_classifier'
$classifierLog = Join-Path $RunDir 'classifier_run.log'
$classifierExit = 990
if($PythonExe -and (Test-Path $targetClassifier)){
  try{
    if($PythonExe.ToLower().EndsWith('py.exe')){ & $PythonExe -3 $targetClassifier 2>&1 | Tee-Object -FilePath $classifierLog } else { & $PythonExe $targetClassifier 2>&1 | Tee-Object -FilePath $classifierLog }
    $classifierExit = $LASTEXITCODE
  }catch{ $classifierExit=991; ('EXCEPTION=' + $_.Exception.Message) | Add-Content -Encoding UTF8 $classifierLog }
}else{ 'classifier not runnable' | Set-Content -Encoding UTF8 $classifierLog }
Slot 'slot_04_classifier_run' $(if($classifierExit -eq 0){'completed'}else{'blocked'}) @('exit=' + $classifierExit, 'log=' + $classifierLog)

B 'running_deep_qa'
$qaLog = Join-Path $RunDir 'deep_qa_run.log'
$qaExit = 990
if($PythonExe -and (Test-Path $targetQA)){
  try{
    if($PythonExe.ToLower().EndsWith('py.exe')){ & $PythonExe -3 $targetQA 2>&1 | Tee-Object -FilePath $qaLog } else { & $PythonExe $targetQA 2>&1 | Tee-Object -FilePath $qaLog }
    $qaExit = $LASTEXITCODE
  }catch{ $qaExit=991; ('EXCEPTION=' + $_.Exception.Message) | Add-Content -Encoding UTF8 $qaLog }
}else{ 'deep qa not runnable' | Set-Content -Encoding UTF8 $qaLog }
Slot 'slot_05_deep_qa_run' $(if($qaExit -eq 0){'completed'}else{'blocked'}) @('exit=' + $qaExit, 'log=' + $qaLog)

B 'parallel_slots'
$jobs=@()
$jobs += Start-Job -Name 'slot_06_inputs' -ScriptBlock { param($InputDir,$SlotsDir,$TaskId) $lines=@(); foreach($n in @('london_parcels_geometry.geojson','market_3110.csv','voa_london.csv')){ $p=Join-Path $InputDir $n; $lines += ($n + '|exists=' + (Test-Path $p) + '|bytes=' + $(if(Test-Path $p){(Get-Item $p).Length}else{0})) }; @('# slot_06_inputs','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_06_inputs.md') } -ArgumentList $InputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_07_outputs' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $lines=@(); foreach($n in @('london_6color.geojson','london_6color.csv','london_6color_summary.csv','london_6color_confidence_summary.csv')){ $p=Join-Path $OutputDir $n; $lines += ($n + '|exists=' + (Test-Path $p) + '|bytes=' + $(if(Test-Path $p){(Get-Item $p).Length}else{0})) }; @('# slot_07_outputs','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_07_outputs.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_08_summary_csv' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir 'london_6color_summary.csv'; $lines=@(); if(Test-Path $p){$lines=Get-Content -Encoding UTF8 $p}else{$lines=@('missing')}; @('# slot_08_summary_csv','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_08_summary_csv.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_09_conf_csv' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir 'london_6color_confidence_summary.csv'; $lines=@(); if(Test-Path $p){$lines=Get-Content -Encoding UTF8 $p}else{$lines=@('missing')}; @('# slot_09_conf_csv','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_09_conf_csv.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_10_qa_inventory' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $qa=Join-Path $OutputDir 'qa'; $lines=@('qa_exists='+(Test-Path $qa)); if(Test-Path $qa){ Get-ChildItem $qa -File | Sort-Object Name | ForEach-Object { $lines += ($_.Name + '|bytes=' + $_.Length) } }; @('# slot_10_qa_inventory','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_10_qa_inventory.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_11_low_conf' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir 'qa\qa_low_confidence_sample.csv'; $lines=@(); if(Test-Path $p){$lines += 'rows=' + @((Import-Csv $p)).Count; $lines += (Get-Content -TotalCount 6 -Encoding UTF8 $p)}else{$lines+='missing'}; @('# slot_11_low_conf','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_11_low_conf.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_12_key_coverage' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir 'qa\qa_key_coverage.csv'; $lines=@(); if(Test-Path $p){$lines=Get-Content -Encoding UTF8 $p}else{$lines=@('missing')}; @('# slot_12_key_coverage','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_12_key_coverage.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_13_keyword_matrix' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir 'qa\qa_keyword_hit_matrix.csv'; $lines=@(); if(Test-Path $p){$lines=Get-Content -Encoding UTF8 $p}else{$lines=@('missing')}; @('# slot_13_keyword_matrix','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_13_keyword_matrix.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_14_local_authority' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir 'qa\qa_local_authority_class_summary.csv'; $lines=@(); if(Test-Path $p){$lines=Get-Content -Encoding UTF8 $p -TotalCount 80}else{$lines=@('missing')}; @('# slot_14_local_authority','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_14_local_authority.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_15_area' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir 'qa\qa_area_by_class_summary.csv'; $lines=@(); if(Test-Path $p){$lines=Get-Content -Encoding UTF8 $p}else{$lines=@('missing')}; @('# slot_15_area','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_15_area.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_16_geojson_features' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir 'london_6color.geojson'; $lines=@(); try{ if(Test-Path $p){ $j=Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json; $lines += 'features=' + $j.features.Count; $lines += 'type=' + $j.type }else{$lines+='missing'} }catch{$lines+='parse_error=' + $_.Exception.Message}; @('# slot_16_geojson_features','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_16_geojson_features.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_17_logs' -ScriptBlock { param($LogDirPlan,$SlotsDir,$TaskId) $lines=@(); foreach($n in @('build.log','deep_qa.log')){ $p=Join-Path $LogDirPlan $n; $lines += '--- ' + $n + ' ---'; if(Test-Path $p){ $lines += Get-Content -Tail 60 -Encoding UTF8 $p } else { $lines += 'missing' } }; @('# slot_17_logs','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_17_logs.md') } -ArgumentList $LogDirPlan,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_18_git_after' -ScriptBlock { param($Bridge,$SlotsDir,$TaskId) Set-Location $Bridge; $out=git status --short 2>&1 | Out-String; @('# slot_18_git_after','TASK_ID='+$TaskId,'RESULT=completed','',$out) | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_18_git_after.md') } -ArgumentList $Bridge,$SlotsDir,$TaskId
Wait-Job $jobs -Timeout 1200 | Out-Null
Receive-Job $jobs -ErrorAction SilentlyContinue | Out-Null
Remove-Job $jobs -Force -ErrorAction SilentlyContinue

$csvOut=Join-Path $OutputDir 'london_6color.csv'
$geoOut=Join-Path $OutputDir 'london_6color.geojson'
$summaryCsv=Join-Path $OutputDir 'london_6color_summary.csv'
$confCsv=Join-Path $OutputDir 'london_6color_confidence_summary.csv'
$qaReport=Join-Path $OutputDir 'qa\PLAN_L_DEEP_QA_REPORT.md'
$rowsOut=Rows $csvOut
$features=JsonFeatures $geoOut
$complete = ($classifierExit -eq 0 -and $qaExit -eq 0 -and (Test-Path $summaryCsv) -and (Test-Path $confCsv) -and $rowsOut -gt 0)
@('metric,value','classifier_exit,'+$classifierExit,'deep_qa_exit,'+$qaExit,'classified_rows,'+$rowsOut,'geojson_features,'+$features,'summary_exists,'+(Test-Path $summaryCsv),'confidence_summary_exists,'+(Test-Path $confCsv),'qa_report_exists,'+(Test-Path $qaReport),'slots,18') | Set-Content -Encoding UTF8 $Score
W '## Consolidated result'
W ('CLASSIFIER_EXIT=' + $classifierExit)
W ('DEEP_QA_EXIT=' + $qaExit)
W ('CLASSIFIED_ROWS=' + $rowsOut)
W ('GEOJSON_FEATURES=' + $features)
W ('QA_REPORT=' + $qaReport)
if(Test-Path $summaryCsv){ W '## Class summary'; Get-Content -Encoding UTF8 $summaryCsv | ForEach-Object { W $_ } }
if(Test-Path $confCsv){ W '## Confidence summary'; Get-Content -Encoding UTF8 $confCsv | ForEach-Object { W $_ } }
if(Test-Path $qaReport){ W '## Deep QA report head'; Get-Content -Encoding UTF8 $qaReport -TotalCount 80 | ForEach-Object { W $_ } }
$result = if($complete){'completed_deep_parallel_qa'}else{'needs_attention_deep_parallel_qa'}
@('TASK=' + $TaskId,'RESULT=' + $result,'CLASSIFIER_EXIT=' + $classifierExit,'DEEP_QA_EXIT=' + $qaExit,'CLASSIFIED_ROWS=' + $rowsOut,'GEOJSON_FEATURES=' + $features,'RUN_DIR=' + $RunDir,'SLOTS_DIR=' + $SlotsDir,'QA_REPORT=' + $qaReport,'NEXT_ACTION=Review ai-results summary and QA csv files; then expand matching rules or package final outputs.','NEXT_COMMAND=devam et') | Set-Content -Encoding UTF8 $Status
B 'finished'
W 'NEXT_COMMAND=devam et'
exit 0
