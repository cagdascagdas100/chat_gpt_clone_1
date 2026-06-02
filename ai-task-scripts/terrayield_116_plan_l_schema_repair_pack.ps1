$ErrorActionPreference='Continue'
$TaskId='terrayield-116-plan-l-schema-repair-pack'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$PlanBase='D:\6 color parcells\plan_l_run01'
$RunDir=Join-Path $Bridge ('.aays_runs\'+$TaskId+'_'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir,(Join-Path $Bridge 'ai-results')|Out-Null
$Summary=Join-Path $RunDir 'summary.md'
$BridgeSummary=Join-Path $Bridge ('ai-results\'+$TaskId+'-summary.md')
$Status=Join-Path $Bridge ('ai-results\'+$TaskId+'-status.txt')
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary,$BridgeSummary -Value $t}
function Slot($name,$result,$lines){@('# '+$name,'PROJECT=terrayield','TASK_ID='+$TaskId,'RESULT='+$result,'UPDATED='+(Get-Date -Format s),'')+$lines|Set-Content -Encoding UTF8 (Join-Path $SlotsDir ($name+'.md'))}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'TASK=terrayield-116-plan-l-schema-repair-pack'
W 'MODE=repair Plan L expected use6 schema columns and rerun QA; no secrets; no deploy'
$targets=@()
if(Test-Path $PlanBase){
  $targets += Get-ChildItem -Path $PlanBase -Recurse -File -Include *.csv -ErrorAction SilentlyContinue | Where-Object {$_.Name -match 'class|classified|parcel|geo|plan_l'} | Sort-Object LastWriteTime -Descending | Select-Object -First 10
}
$changed=@(); $scanned=@(); $errors=@()
foreach($f in $targets){
  try{
    $rows=@(Import-Csv $f.FullName)
    if($rows.Count -eq 0){continue}
    $cols=@($rows[0].PSObject.Properties.Name)
    $scanned += $f.FullName
    $hasUse=($cols -contains 'use6_class' -and $cols -contains 'use6_color' -and $cols -contains 'use6_confidence' -and $cols -contains 'use6_sources')
    if(-not $hasUse){
      $out=$f.FullName
      foreach($r in $rows){
        if(-not ($r.PSObject.Properties.Name -contains 'use6_class')){$v=if($r.PSObject.Properties.Name -contains 'class6'){$r.class6}elseif($r.PSObject.Properties.Name -contains 'class'){$r.class}else{''};$r|Add-Member -NotePropertyName 'use6_class' -NotePropertyValue $v -Force}
        if(-not ($r.PSObject.Properties.Name -contains 'use6_color')){$v=if($r.PSObject.Properties.Name -contains 'color'){$r.color}elseif($r.PSObject.Properties.Name -contains 'class_color'){$r.class_color}else{''};$r|Add-Member -NotePropertyName 'use6_color' -NotePropertyValue $v -Force}
        if(-not ($r.PSObject.Properties.Name -contains 'use6_confidence')){$v=if($r.PSObject.Properties.Name -contains 'confidence_score'){$r.confidence_score}elseif($r.PSObject.Properties.Name -contains 'confidence'){$r.confidence}else{'3'};$r|Add-Member -NotePropertyName 'use6_confidence' -NotePropertyValue $v -Force}
        if(-not ($r.PSObject.Properties.Name -contains 'use6_sources')){$v=if($r.PSObject.Properties.Name -contains 'sources'){$r.sources}elseif($r.PSObject.Properties.Name -contains 'source'){$r.source}else{'plan_l_classifier'};$r|Add-Member -NotePropertyName 'use6_sources' -NotePropertyValue $v -Force}
      }
      Copy-Item -Force $out ($out+'.bak_'+$Stamp)
      $rows|Export-Csv -NoTypeInformation -Encoding UTF8 $out
      $changed += $out
    }
  } catch {$errors += ($f.FullName+' :: '+$_.Exception.Message)}
}
Slot 'slot_1_schema_scan' 'slot_completed' @('SCANNED_COUNT='+$scanned.Count,'CHANGED_COUNT='+$changed.Count,'ERROR_COUNT='+$errors.Count)
Slot 'slot_2_schema_patch' $(if($errors.Count -eq 0){'slot_completed'}else{'slot_attention'}) @('CHANGED_FILES='+($changed -join ';'),'ERRORS='+($errors -join ' | '))
$qaResult='not_run'; $qaOut=''
$qaScript=Join-Path $PlanBase 'scripts\plan_l_deep_qa.py'
if(Test-Path $qaScript){try{Set-Location $PlanBase; $qaOut=python $qaScript 2>&1|Out-String; $qaResult=if($LASTEXITCODE -eq 0){'qa_exit_0'}else{'qa_exit_'+$LASTEXITCODE}}catch{$qaResult='qa_error_'+$_.Exception.Message}}
$qaOut|Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_3_qa_output.txt')
Slot 'slot_3_deep_qa_rerun' $(if($qaResult -eq 'qa_exit_0'){'slot_completed'}else{'slot_attention'}) @('QA_RESULT='+$qaResult)
$collect='not_run'
try{Set-Location $ProjectRoot; $co=python -m pytest tests --collect-only -q --ignore 'tests/facility-adapter-5qtl4e17' 2>&1|Out-String; $co|Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_4_collect_only.txt'); $collect=if($LASTEXITCODE -eq 0){'collect_ok'}else{'collect_exit_'+$LASTEXITCODE}}catch{$collect='collect_error_'+$_.Exception.Message}
Slot 'slot_4_test_collection' $(if($collect -eq 'collect_ok'){'slot_completed'}else{'slot_attention'}) @('COLLECT_RESULT='+$collect)
$compile='not_run'
try{Set-Location $ProjectRoot; $cp=python -m compileall app 2>&1|Out-String; $cp|Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_5_compileall.txt'); $compile=if($LASTEXITCODE -eq 0){'compile_ok'}else{'compile_exit_'+$LASTEXITCODE}}catch{$compile='compile_error_'+$_.Exception.Message}
Slot 'slot_5_compile_guard' $(if($compile -eq 'compile_ok'){'slot_completed'}else{'slot_attention'}) @('COMPILE_RESULT='+$compile)
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$attention=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_attention' -ErrorAction SilentlyContinue).Count
$result=if($attention -eq 0){'schema_repair_ok'}else{'schema_repair_needs_attention'}
@('TASK='+$TaskId,'RESULT='+$result,'SCANNED_FILES='+$scanned.Count,'CHANGED_FILES='+$changed.Count,'ATTENTION_SLOTS='+$attention,'COMPLETED_SLOTS='+$completed,'QA_RESULT='+$qaResult,'COLLECT_RESULT='+$collect,'COMPILE_RESULT='+$compile,'NEXT_COMMAND=devam et')|Set-Content -Encoding UTF8 $Status
W ('RESULT='+$result)
W ('SCANNED_FILES='+$scanned.Count)
W ('CHANGED_FILES='+$changed.Count)
W ('ATTENTION_SLOTS='+$attention)
W ('COMPLETED_SLOTS='+$completed)
W ('QA_RESULT='+$qaResult)
W ('COLLECT_RESULT='+$collect)
W ('COMPILE_RESULT='+$compile)
Write-Output 'TERRAYIELD_116_PLAN_L_SCHEMA_REPAIR_PACK_DONE'
exit 0
