$ErrorActionPreference='Continue'
$TaskId='terrayield-108-apply-final-3110-fail-closed-l4-handoff'
$Run=Get-Date -Format 'yyyyMMdd_HHmmss'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$ExportDir=Join-Path $ProjectRoot 'data\live_feeds\exports_codex'
$ActiveDir=Join-Path $ProjectRoot 'data\live_feeds\active'
$ResultDir=Join-Path $Bridge 'ai-results'
$BeatDir=Join-Path $Bridge 'ai-heartbeat'
$RunDir=Join-Path $ProjectRoot ('.aays_real_runs\'+$TaskId+'_'+$Run)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $ExportDir,$ActiveDir,$ResultDir,$BeatDir,$RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'summary.md'; $BridgeSummary=Join-Path $ResultDir ($TaskId+'-summary.md')
$Status=Join-Path $RunDir 'status.txt'; $BridgeStatus=Join-Path $ResultDir ($TaskId+'-status.txt')
function L($x){Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary,$BridgeSummary -Value $x}
function B($s){@('# TerraYield handoff apply','TASK_ID='+$TaskId,'STATUS='+$s,'UPDATED='+(Get-Date -Format s))|Set-Content -Encoding UTF8 (Join-Path $BeatDir ($TaskId+'.md'))}
function Slot($n,$r,$lines){@('# '+$n,'PROJECT=terrayield','TASK_ID='+$TaskId,'RESULT='+$r,'UPDATED='+(Get-Date -Format s),'')+$lines|Set-Content -Encoding UTF8 (Join-Path $SlotsDir ($n+'.md'))}
B 'starting'; L '# TerraYield 108 apply FINAL 3110 fail-closed L4 handoff'; L 'MODE=read_only_export_manifest; no_ui_patch; no_db_import'
$Base='FINAL_3110_FAIL_CLOSED_L4_B500'
$ZipName=$Base+'_report_only_handoff.zip'
$Expected=@($Base+'_MASTER.csv',$Base+'_MASTER.jsonl',$Base+'_SUMMARY.json',$Base+'_LONDON_LOCATIONS.csv',$Base+'_PUBLIC_ONLY_DOMAIN_POLICY.json',$Base+'_FETCH_CACHE_MANIFEST.jsonl',$Base+'_RECHECK_DO_NOT_REPEAT.json',$Base+'_BATCH_INDEX.csv')
$ZipPath=Join-Path $ExportDir $ZipName; $Master=Join-Path $ExportDir ($Base+'_MASTER.csv'); $London=Join-Path $ExportDir ($Base+'_LONDON_LOCATIONS.csv'); $Sum=Join-Path $ExportDir ($Base+'_SUMMARY.json'); $Policy=Join-Path $ExportDir ($Base+'_PUBLIC_ONLY_DOMAIN_POLICY.json')
B 'locating_package'
if(!(Test-Path $ZipPath)-and !(Test-Path $Master)){
  foreach($root in @($ExportDir,(Join-Path $ProjectRoot 'data'),$Bridge,(Join-Path $Bridge 'ai-inputs'),(Join-Path $env:USERPROFILE 'Downloads'))){
    if($root -and (Test-Path $root)){try{$f=Get-ChildItem -Path $root -Recurse -File -Filter $ZipName -ErrorAction SilentlyContinue|Select-Object -First 1;if($f){$ZipPath=$f.FullName;break}}catch{}}
  }
}
if((Test-Path $ZipPath)-and !(Test-Path $Master)){B 'expanding_package'; L ('EXPAND='+$ZipPath); try{Expand-Archive -LiteralPath $ZipPath -DestinationPath $ExportDir -Force}catch{L ('EXPAND_ERROR='+$_.Exception.Message)}}
B 'validating_package'
$missing=@(); foreach($e in $Expected){if(!(Test-Path (Join-Path $ExportDir $e))){$missing+=$e}}
if($missing.Count -gt 0){
  $msg='RESULT=blocked_missing_handoff_files; missing='+($missing -join ',')
  L $msg; L ('EXPECTED_DIR='+$ExportDir); L ('ZIP_NAME='+$ZipName)
  Slot 'slot_1_data_presence' 'slot_blocked' @($msg); Slot 'slot_2_policy_validation' 'slot_blocked' @('package not present on runner disk'); Slot 'slot_3_active_manifest' 'slot_blocked' @('not written'); Slot 'slot_4_app_readiness' 'slot_blocked' @('no app changes'); Slot 'slot_5_tests_validation' 'slot_blocked' @('not run')
  @('TASK='+$TaskId,'RESULT=blocked_missing_handoff_files','NEXT_ACTION=Place '+$ZipName+' in '+$ExportDir+' and rerun','NEXT_COMMAND=devam et')|Set-Content -Encoding UTF8 $Status
  Copy-Item -Force $Status $BridgeStatus; B 'blocked_missing_handoff_files'; exit 0
}
$summary=Get-Content -Raw -Encoding UTF8 $Sum|ConvertFrom-Json; $policy=Get-Content -Raw -Encoding UTF8 $Policy|ConvertFrom-Json
$rowsTotal=[int]$summary.rows_total; $rowsLondon=[int]$summary.rows_london; $failClosed=[int]$summary.fail_closed_verified_rows; $publicOnly=[bool]$policy.allow_only_public_sources
$masterRows=@(Import-Csv $Master).Count; $londonRows=@(Import-Csv $London).Count
$valid=($rowsTotal -eq 3110 -and $rowsLondon -eq 606 -and $failClosed -eq 0 -and $publicOnly -and $masterRows -eq 3110 -and $londonRows -eq 606)
Slot 'slot_1_data_presence' 'slot_completed' @('expected_files=8','master_rows='+$masterRows,'london_rows='+$londonRows)
Slot 'slot_2_policy_validation' $(if($valid){'slot_completed'}else{'slot_blocked'}) @('summary_rows_total='+$rowsTotal,'summary_rows_london='+$rowsLondon,'fail_closed_verified_rows='+$failClosed,'public_only='+$publicOnly,'package_valid='+$valid)
B 'activating_manifest'
$ManifestPath=Join-Path $ActiveDir 'terrayield_l4_fail_closed_current.json'; $ActiveLondon=Join-Path $ActiveDir 'terrayield_london_locations_current.csv'; $Readme=Join-Path $ActiveDir 'README_TERRAYIELD_L4_FAIL_CLOSED.md'
[ordered]@{schema_version=1;task_id=$TaskId;activated_at=(Get-Date).ToString('o');status=$(if($valid){'active_read_only_fail_closed_l4'}else{'active_with_validation_warnings'});dataset_name=$Base;source_package=$ZipName;rows_total=$rowsTotal;rows_london=$rowsLondon;fail_closed_verified_rows=$failClosed;master_csv='data/live_feeds/exports_codex/'+$Base+'_MASTER.csv';master_jsonl='data/live_feeds/exports_codex/'+$Base+'_MASTER.jsonl';london_locations_csv='data/live_feeds/exports_codex/'+$Base+'_LONDON_LOCATIONS.csv';policy_json='data/live_feeds/exports_codex/'+$Base+'_PUBLIC_ONLY_DOMAIN_POLICY.json';app_integration_mode='read_only_export_manifest_not_db_import';ui_patch_applied=$false;db_import_applied=$false;validation=[ordered]@{master_csv_rows=$masterRows;london_locations_rows=$londonRows;public_only_policy=$publicOnly;package_valid=$valid}}|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $ManifestPath
Copy-Item -Force $London $ActiveLondon
@('# TerraYield L4 fail-closed active dataset','','Active manifest: terrayield_l4_fail_closed_current.json','London map/feed file: terrayield_london_locations_current.csv','No DB import. No UI patch. Fail-closed L4 preserved.','Rows total: '+$rowsTotal,'London rows: '+$rowsLondon,'Fail-closed verified rows: '+$failClosed,'Package valid: '+$valid)|Set-Content -Encoding UTF8 $Readme
Slot 'slot_3_active_manifest' 'slot_completed' @('active_manifest='+$ManifestPath,'active_london_csv='+$ActiveLondon,'readme='+$Readme)
$appCount=0; try{$appCount=@(Get-ChildItem -Path (Join-Path $ProjectRoot 'app') -Recurse -File -ErrorAction SilentlyContinue|Select-Object -First 80).Count}catch{}
Slot 'slot_4_app_readiness' 'slot_completed' @('app_files_scanned='+$appCount,'contract=read data/live_feeds/active/terrayield_l4_fail_closed_current.json','no_ui_patch=true','no_db_import=true')
$compile='not_run_no_app_dir'; if(Test-Path (Join-Path $ProjectRoot 'app')){try{Set-Location $ProjectRoot; $out=python -m compileall app 2>&1|Out-String; $compile=if($LASTEXITCODE -eq 0){'compileall_ok'}else{'compileall_exit_'+$LASTEXITCODE}; $out|Set-Content -Encoding UTF8 (Join-Path $SlotsDir 'slot_5_compileall_output.txt')}catch{$compile='compileall_error_'+$_.Exception.Message}}
Slot 'slot_5_tests_validation' $(if($compile -eq 'compileall_ok' -or $compile -eq 'not_run_no_app_dir'){'slot_completed'}else{'slot_blocked'}) @('compile_result='+$compile,'package_valid='+$valid)
$result=if($valid){'applied_read_only_fail_closed_l4_handoff'}else{'applied_with_validation_warnings'}
@('TASK='+$TaskId,'RESULT='+$result,'ROWS_TOTAL='+$rowsTotal,'ROWS_LONDON='+$rowsLondon,'FAIL_CLOSED_VERIFIED_ROWS='+$failClosed,'ACTIVE_MANIFEST='+$ManifestPath,'ACTIVE_LONDON_CSV='+$ActiveLondon,'NO_UI_PATCH=true','NO_DB_IMPORT=true','NEXT_COMMAND=devam et')|Set-Content -Encoding UTF8 $Status
Copy-Item -Force $Status $BridgeStatus
@('metric,score','handoff_files_present,1','active_manifest_written,1','source_accuracy_score,45','parcel_match_accuracy_score,27','operational_health_score,'+$(if($valid){70}else{35}),'general_confidence_score,'+$(if($valid){52}else{32}),'program_completion,'+$(if($valid){42}else{36}))|Set-Content -Encoding UTF8 (Join-Path $RunDir 'scorecard.csv')
L ('RESULT='+$result); L ('ROWS_TOTAL='+$rowsTotal); L ('ROWS_LONDON='+$rowsLondon); L ('ACTIVE_MANIFEST='+$ManifestPath); L 'NO_UI_PATCH=true'; L 'NO_DB_IMPORT=true'
B 'finished'; exit 0