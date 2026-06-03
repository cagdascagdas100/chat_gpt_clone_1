$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-112-plan-l-recovery-final-pack'
$Run = Get-Date -Format 'yyyyMMdd_HHmmss'
$Bridge = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlanBase = 'D:\6 color parcells\plan_l_run01'
$InputDir = Join-Path $PlanBase 'input'
$OutputDir = Join-Path $PlanBase 'output'
$ScriptDir = Join-Path $PlanBase 'scripts'
$PlanLogDir = Join-Path $PlanBase 'logs'
$QaDir = Join-Path $OutputDir 'qa'
$FinalDir = Join-Path $PlanBase ('final_packages\' + $TaskId + '_' + $Run)
$ResultDir = Join-Path $Bridge 'ai-results'
$BeatDir = Join-Path $Bridge 'ai-heartbeat'
$RunDir = Join-Path $Bridge ('.aays_runs\' + $TaskId + '_' + $Run)
$SlotsDir = Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $ResultDir,$BeatDir,$RunDir,$SlotsDir,$ScriptDir,$OutputDir,$PlanLogDir,$QaDir,$FinalDir | Out-Null
$Summary = Join-Path $ResultDir ($TaskId + '-summary.md')
$Status = Join-Path $ResultDir ($TaskId + '-status.txt')
$Score = Join-Path $ResultDir ($TaskId + '-scorecard.csv')
function W([string]$x){ Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x }
function B([string]$s){ @('# AAYS Heartbeat','TASK_ID=' + $TaskId,'STATUS=' + $s,'UPDATED=' + (Get-Date -Format s),'PLAN_BASE=' + $PlanBase) | Set-Content -Encoding UTF8 (Join-Path $BeatDir ($TaskId + '.md')) }
function Slot([string]$n,[string]$r,[string[]]$lines){ @('# ' + $n,'TASK_ID=' + $TaskId,'RESULT=' + $r,'UPDATED=' + (Get-Date -Format s),'') + $lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir ($n + '.md')) }
function CsvRows([string]$p){ try{ if(Test-Path $p){ return @((Import-Csv -LiteralPath $p)).Count } }catch{ return -1 } return 0 }
function JsonFeatureCount([string]$p){ try{ if(Test-Path $p){ $j=Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json; return $j.features.Count } }catch{ return -1 } return 0 }
function FileLine([string]$p){ if(Test-Path $p){ return ((Get-Item $p).FullName + '|bytes=' + (Get-Item $p).Length + '|sha256=' + (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash) } return ($p + '|missing') }
B 'starting'
W '# TerraYield 112 Plan L Recovery Final Pack'
W 'MODE=single_devam_maximal_safe_batch; recover_previous; rerun_if_needed; build_final_package; no_secrets; no_deploy'
W ('PLAN_BASE=' + $PlanBase)
W ('FINAL_DIR=' + $FinalDir)

$sourceClassifier = Join-Path $Bridge 'ai-task-scripts\build_london_6color_plan_l.py'
$targetClassifier = Join-Path $ScriptDir 'build_london_6color.py'
$sourceQA = Join-Path $Bridge 'ai-task-scripts\plan_l_deep_qa.py'
$targetQA = Join-Path $ScriptDir 'plan_l_deep_qa.py'
if(Test-Path $sourceClassifier){ Copy-Item -Force $sourceClassifier $targetClassifier }
if(Test-Path $sourceQA){ Copy-Item -Force $sourceQA $targetQA }
Slot 'slot_01_sync_sources' 'completed' @((FileLine $targetClassifier),(FileLine $targetQA))

$PythonExe=$null
foreach($c in @('python','py')){ $cmd=Get-Command $c -ErrorAction SilentlyContinue; if($cmd){ $PythonExe=$cmd.Source; break } }
Slot 'slot_02_python' $(if($PythonExe){'completed'}else{'blocked'}) @('python_exe=' + $(if($PythonExe){$PythonExe}else{'not_found'}))

$csvOut=Join-Path $OutputDir 'london_6color.csv'
$geoOut=Join-Path $OutputDir 'london_6color.geojson'
$summaryCsv=Join-Path $OutputDir 'london_6color_summary.csv'
$confCsv=Join-Path $OutputDir 'london_6color_confidence_summary.csv'
$needRun = (!(Test-Path $csvOut) -or !(Test-Path $geoOut) -or !(Test-Path $summaryCsv) -or !(Test-Path $confCsv) -or (CsvRows $csvOut) -le 0)
$classifierExit = 999
$classifierLog = Join-Path $RunDir 'classifier_run.log'
if($needRun -and $PythonExe -and (Test-Path $targetClassifier)){
  B 'running_classifier_recovery'
  try{ if($PythonExe.ToLower().EndsWith('py.exe')){ & $PythonExe -3 $targetClassifier 2>&1 | Tee-Object -FilePath $classifierLog } else { & $PythonExe $targetClassifier 2>&1 | Tee-Object -FilePath $classifierLog }; $classifierExit=$LASTEXITCODE }catch{ $classifierExit=998; ('EXCEPTION=' + $_.Exception.Message) | Add-Content -Encoding UTF8 $classifierLog }
}else{
  $classifierExit = if($needRun){997}else{0}
  ('need_run=' + $needRun + '; skipped_or_not_runnable') | Set-Content -Encoding UTF8 $classifierLog
}
Slot 'slot_03_classifier_recovery' $(if($classifierExit -eq 0){'completed'}else{'blocked'}) @('need_run=' + $needRun,'exit=' + $classifierExit,'log=' + $classifierLog)

$qaExit=999
$qaLog=Join-Path $RunDir 'deep_qa_run.log'
if($PythonExe -and (Test-Path $targetQA)){
  B 'running_deep_qa'
  try{ if($PythonExe.ToLower().EndsWith('py.exe')){ & $PythonExe -3 $targetQA 2>&1 | Tee-Object -FilePath $qaLog } else { & $PythonExe $targetQA 2>&1 | Tee-Object -FilePath $qaLog }; $qaExit=$LASTEXITCODE }catch{ $qaExit=998; ('EXCEPTION=' + $_.Exception.Message) | Add-Content -Encoding UTF8 $qaLog }
}else{ $qaExit=997; 'deep qa not runnable' | Set-Content -Encoding UTF8 $qaLog }
Slot 'slot_04_deep_qa' $(if($qaExit -eq 0){'completed'}else{'blocked'}) @('exit=' + $qaExit,'log=' + $qaLog)

B 'launching_wide_parallel_slots'
$jobs=@()
$jobs += Start-Job -Name 'slot_05_tree_inventory' -ScriptBlock { param($PlanBase,$SlotsDir,$TaskId) $lines=@(); foreach($d in @('input','scripts','output','output\qa','logs')){ $p=Join-Path $PlanBase $d; $lines += ('DIR ' + $d + ' exists=' + (Test-Path $p)); if(Test-Path $p){ Get-ChildItem $p -File -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object { $lines += ('  ' + $_.Name + '|bytes=' + $_.Length) } } }; @('# slot_05_tree_inventory','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_05_tree_inventory.md') } -ArgumentList $PlanBase,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_06_output_hashes' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $lines=@(); foreach($n in @('london_6color.geojson','london_6color.csv','london_6color_summary.csv','london_6color_confidence_summary.csv')){ $p=Join-Path $OutputDir $n; if(Test-Path $p){ $lines += ($n + '|bytes=' + (Get-Item $p).Length + '|sha256=' + (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash) } else { $lines += ($n + '|missing') } }; @('# slot_06_output_hashes','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_06_output_hashes.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_07_row_counts' -ScriptBlock { param($OutputDir,$InputDir,$SlotsDir,$TaskId) function R($p){ try{ if(Test-Path $p){ return @((Import-Csv -LiteralPath $p)).Count } }catch{ return -1 } return 0 }; $lines=@(); foreach($p in @((Join-Path $InputDir 'market_3110.csv'),(Join-Path $InputDir 'voa_london.csv'),(Join-Path $OutputDir 'london_6color.csv'))){ $lines += ((Split-Path $p -Leaf) + '|rows=' + (R $p)) }; try{ $g=Join-Path $OutputDir 'london_6color.geojson'; if(Test-Path $g){ $j=Get-Content -Raw -Encoding UTF8 $g | ConvertFrom-Json; $lines += ('geojson_features=' + $j.features.Count) }}catch{ $lines+='geojson_features=parse_error' }; @('# slot_07_row_counts','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_07_row_counts.md') } -ArgumentList $OutputDir,$InputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_08_class_summary' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir 'london_6color_summary.csv'; $lines=if(Test-Path $p){Get-Content -Encoding UTF8 $p}else{@('missing')}; @('# slot_08_class_summary','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_08_class_summary.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_09_conf_summary' -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir 'london_6color_confidence_summary.csv'; $lines=if(Test-Path $p){Get-Content -Encoding UTF8 $p}else{@('missing')}; @('# slot_09_conf_summary','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_09_conf_summary.md') } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_10_qa_report' -ScriptBlock { param($QaDir,$SlotsDir,$TaskId) $p=Join-Path $QaDir 'PLAN_L_DEEP_QA_REPORT.md'; $lines=if(Test-Path $p){Get-Content -Encoding UTF8 $p -TotalCount 140}else{@('missing')}; @('# slot_10_qa_report','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_10_qa_report.md') } -ArgumentList $QaDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_11_qa_json' -ScriptBlock { param($QaDir,$SlotsDir,$TaskId) $p=Join-Path $QaDir 'plan_l_deep_qa_report.json'; $lines=@(); try{ if(Test-Path $p){ $j=Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json; $lines += 'classified_rows=' + $j.counts.classified_rows; $lines += 'market_rows=' + $j.counts.market_rows; $lines += 'voa_rows=' + $j.counts.voa_rows; $lines += 'warnings=' + (($j.warnings | ForEach-Object { $_ }) -join '; ') } else { $lines+='missing' } }catch{ $lines += 'parse_error=' + $_.Exception.Message }; @('# slot_11_qa_json','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_11_qa_json.md') } -ArgumentList $QaDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_12_low_conf_stats' -ScriptBlock { param($QaDir,$SlotsDir,$TaskId) $p=Join-Path $QaDir 'qa_low_confidence_sample.csv'; $lines=@(); try{ if(Test-Path $p){ $rows=@(Import-Csv $p); $lines+='sample_rows='+$rows.Count; $lines += ($rows | Group-Object use6_class | Sort-Object Count -Descending | ForEach-Object { $_.Name + '=' + $_.Count }) }else{$lines+='missing'} }catch{$lines+='error='+$_.Exception.Message}; @('# slot_12_low_conf_stats','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_12_low_conf_stats.md') } -ArgumentList $QaDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_13_key_coverage' -ScriptBlock { param($QaDir,$SlotsDir,$TaskId) $p=Join-Path $QaDir 'qa_key_coverage.csv'; $lines=if(Test-Path $p){Get-Content -Encoding UTF8 $p}else{@('missing')}; @('# slot_13_key_coverage','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_13_key_coverage.md') } -ArgumentList $QaDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_14_keyword_matrix' -ScriptBlock { param($QaDir,$SlotsDir,$TaskId) $p=Join-Path $QaDir 'qa_keyword_hit_matrix.csv'; $lines=if(Test-Path $p){Get-Content -Encoding UTF8 $p}else{@('missing')}; @('# slot_14_keyword_matrix','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_14_keyword_matrix.md') } -ArgumentList $QaDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_15_local_authority_top' -ScriptBlock { param($QaDir,$SlotsDir,$TaskId) $p=Join-Path $QaDir 'qa_local_authority_class_summary.csv'; $lines=if(Test-Path $p){Get-Content -Encoding UTF8 $p -TotalCount 140}else{@('missing')}; @('# slot_15_local_authority_top','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_15_local_authority_top.md') } -ArgumentList $QaDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_16_area_summary' -ScriptBlock { param($QaDir,$SlotsDir,$TaskId) $p=Join-Path $QaDir 'qa_area_by_class_summary.csv'; $lines=if(Test-Path $p){Get-Content -Encoding UTF8 $p}else{@('missing')}; @('# slot_16_area_summary','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_16_area_summary.md') } -ArgumentList $QaDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_17_karma_audit' -ScriptBlock { param($QaDir,$SlotsDir,$TaskId) $p=Join-Path $QaDir 'qa_suspicious_karma_rows.csv'; $lines=@(); if(Test-Path $p){ $lines += 'rows=' + @((Import-Csv $p)).Count; $lines += Get-Content -Encoding UTF8 $p -TotalCount 20 }else{$lines+='missing'}; @('# slot_17_karma_audit','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_17_karma_audit.md') } -ArgumentList $QaDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_18_logs_tail' -ScriptBlock { param($PlanLogDir,$SlotsDir,$TaskId) $lines=@(); foreach($n in @('build.log','deep_qa.log')){ $p=Join-Path $PlanLogDir $n; $lines += '--- ' + $n + ' ---'; if(Test-Path $p){ $lines += Get-Content -Tail 80 -Encoding UTF8 $p } else { $lines += 'missing' } }; @('# slot_18_logs_tail','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_18_logs_tail.md') } -ArgumentList $PlanLogDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_19_previous_results' -ScriptBlock { param($Bridge,$SlotsDir,$TaskId) $r=Join-Path $Bridge 'ai-results'; $lines=@(); foreach($n in @('terrayield-110-plan-l-parallel-expansion-status.txt','terrayield-111-plan-l-deep-parallel-qa-status.txt')){ $p=Join-Path $r $n; $lines += $n + '|exists=' + (Test-Path $p); if(Test-Path $p){ $lines += Get-Content -Encoding UTF8 $p } }; @('# slot_19_previous_results','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_19_previous_results.md') } -ArgumentList $Bridge,$SlotsDir,$TaskId
$jobs += Start-Job -Name 'slot_20_git_health' -ScriptBlock { param($Bridge,$SlotsDir,$TaskId) Set-Location $Bridge; $lines=@(); $lines += 'branch=' + (git branch --show-current 2>&1 | Out-String).Trim(); $lines += 'status='; $lines += (git status --short 2>&1 | Out-String); @('# slot_20_git_health','TASK_ID='+$TaskId,'RESULT=completed','')+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_20_git_health.md') } -ArgumentList $Bridge,$SlotsDir,$TaskId
Wait-Job $jobs -Timeout 1500 | Out-Null
Receive-Job $jobs -ErrorAction SilentlyContinue | Out-Null
Remove-Job $jobs -Force -ErrorAction SilentlyContinue

B 'building_final_package'
$manifest = Join-Path $FinalDir 'PLAN_L_FINAL_MANIFEST.txt'
$copyList = @($targetClassifier,$targetQA,$csvOut,$geoOut,$summaryCsv,$confCsv,(Join-Path $QaDir 'PLAN_L_DEEP_QA_REPORT.md'),(Join-Path $QaDir 'plan_l_deep_qa_report.json'))
foreach($p in $copyList){ if(Test-Path $p){ Copy-Item -Force -LiteralPath $p -Destination $FinalDir } }
if(Test-Path $QaDir){ Copy-Item -Recurse -Force -LiteralPath $QaDir -Destination (Join-Path $FinalDir 'qa_all') }
Copy-Item -Recurse -Force -LiteralPath $SlotsDir -Destination (Join-Path $FinalDir 'runner_slots')
$manifestLines=@('TASK_ID=' + $TaskId,'RUN=' + $Run,'PLAN_BASE=' + $PlanBase,'GENERATED=' + (Get-Date -Format s),'CLASSIFIER_EXIT=' + $classifierExit,'DEEP_QA_EXIT=' + $qaExit,'CSV_ROWS=' + (CsvRows $csvOut),'GEOJSON_FEATURES=' + (JsonFeatureCount $geoOut),'')
Get-ChildItem -File -Recurse $FinalDir | Sort-Object FullName | ForEach-Object { $manifestLines += ($_.FullName.Substring($FinalDir.Length+1) + '|bytes=' + $_.Length + '|sha256=' + (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash) }
$manifestLines | Set-Content -Encoding UTF8 $manifest
$zipPath = Join-Path $PlanBase ('final_packages\' + $TaskId + '_' + $Run + '.zip')
try{ if(Test-Path $zipPath){Remove-Item -Force $zipPath}; Compress-Archive -LiteralPath (Join-Path $FinalDir '*') -DestinationPath $zipPath -Force; $zipOk=Test-Path $zipPath }catch{ $zipOk=$false; ('ZIP_ERROR=' + $_.Exception.Message) | Add-Content -Encoding UTF8 $manifest }
Slot 'slot_21_final_package' $(if($zipOk){'completed'}else{'blocked'}) @('final_dir=' + $FinalDir,'zip=' + $zipPath,'zip_exists=' + $zipOk)

$rowsOut=CsvRows $csvOut
$features=JsonFeatureCount $geoOut
$complete = ($classifierExit -eq 0 -and $qaExit -eq 0 -and $rowsOut -gt 0 -and $features -eq $rowsOut -and (Test-Path $summaryCsv) -and (Test-Path $confCsv) -and $zipOk)
@('metric,value','classifier_exit,'+$classifierExit,'deep_qa_exit,'+$qaExit,'csv_rows,'+$rowsOut,'geojson_features,'+$features,'rows_features_match,'+($features -eq $rowsOut),'summary_exists,'+(Test-Path $summaryCsv),'confidence_summary_exists,'+(Test-Path $confCsv),'final_zip_exists,'+$zipOk,'parallel_slots,21') | Set-Content -Encoding UTF8 $Score
W '## Consolidated final status'
W ('RESULT=' + $(if($complete){'completed_recovery_final_pack'}else{'needs_attention_recovery_final_pack'}))
W ('CLASSIFIER_EXIT=' + $classifierExit)
W ('DEEP_QA_EXIT=' + $qaExit)
W ('CSV_ROWS=' + $rowsOut)
W ('GEOJSON_FEATURES=' + $features)
W ('FINAL_DIR=' + $FinalDir)
W ('FINAL_ZIP=' + $zipPath)
if(Test-Path $summaryCsv){ W '## Class summary'; Get-Content -Encoding UTF8 $summaryCsv | ForEach-Object { W $_ } }
if(Test-Path $confCsv){ W '## Confidence summary'; Get-Content -Encoding UTF8 $confCsv | ForEach-Object { W $_ } }
if(Test-Path (Join-Path $QaDir 'PLAN_L_DEEP_QA_REPORT.md')){ W '## QA report head'; Get-Content -Encoding UTF8 (Join-Path $QaDir 'PLAN_L_DEEP_QA_REPORT.md') -TotalCount 100 | ForEach-Object { W $_ } }
$result = if($complete){'completed_recovery_final_pack'}else{'needs_attention_recovery_final_pack'}
@('TASK=' + $TaskId,'RESULT=' + $result,'CLASSIFIER_EXIT=' + $classifierExit,'DEEP_QA_EXIT=' + $qaExit,'CSV_ROWS=' + $rowsOut,'GEOJSON_FEATURES=' + $features,'FINAL_DIR=' + $FinalDir,'FINAL_ZIP=' + $zipPath,'SLOTS_DIR=' + $SlotsDir,'NEXT_ACTION=If complete, proceed to review/accuracy expansion; if attention needed, inspect slot files and rerun targeted repair.','NEXT_COMMAND=devam et') | Set-Content -Encoding UTF8 $Status
B 'finished'
W 'NEXT_COMMAND=devam et'
exit 0
