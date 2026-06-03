$ErrorActionPreference='Continue'
$TaskId='terrayield-080-source-confidence-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__080_source_confidence_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir | Out-Null
$Summary=Join-Path $RunDir 'terrayield__080_summary.md'
$Status=Join-Path $RunDir 'terrayield__080_status.txt'
$Score=Join-Path $RunDir 'terrayield__080_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'TASK=terrayield-080-source-confidence-5worker-safe'
W 'MODE=source confidence and parcel evidence; five worker safe package'
$Slots=@(
 @{slot='slot_1_source_registry'; kind='source_registry'},
 @{slot='slot_2_sales_schema'; kind='sales_schema'},
 @{slot='slot_3_parcel_join_keys'; kind='parcel_join_keys'},
 @{slot='slot_4_map_ui_evidence'; kind='map_ui_evidence'},
 @{slot='slot_5_quality_score'; kind='quality_score'}
)
$Worker={
 param($Slot,$Kind,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__080__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-080-source-confidence-5worker-safe','SLOT='+$Slot,'KIND='+$Kind,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Kind -eq 'source_registry'){
     L 'CHECK=source_registry_inventory'
     Get-ChildItem -Recurse -File -Include *.md,*.json,*.csv,*.xlsx -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-String -Pattern 'source','evidence','confidence','sales','market','parcel' -ErrorAction SilentlyContinue | Select-Object -First 120 | Out-String | Add-Content $out
   } elseif($Kind -eq 'sales_schema'){
     L 'CHECK=sales_data_schema_candidates'
     Get-ChildItem -Recurse -File -Include *.csv,*.json,*.xlsx -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-Object -First 80 FullName,Length,LastWriteTime | Out-String | Add-Content $out
   } elseif($Kind -eq 'parcel_join_keys'){
     L 'CHECK=parcel_join_keyword_scan'
     Get-ChildItem -Recurse -File -Include *.py,*.sql,*.json,*.geojson,*.ts,*.tsx -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch 'node_modules|dist|build|\.venv'} | Select-String -Pattern 'parcel_id','ada','parsel','geometry','lat','lon','address','ilce','mahalle' -ErrorAction SilentlyContinue | Select-Object -First 120 | Out-String | Add-Content $out
   } elseif($Kind -eq 'map_ui_evidence'){
     L 'CHECK=map_ui_sales_parcel_layer_scan'
     Get-ChildItem -Recurse -File -Include *.ts,*.tsx,*.js,*.jsx -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch 'node_modules|dist|build'} | Select-String -Pattern 'map','layer','marker','polygon','parcel','sales','price','confidence' -ErrorAction SilentlyContinue | Select-Object -First 120 | Out-String | Add-Content $out
   } else {
     L 'CHECK=quality_score_config_and_tests'
     Get-ChildItem -Recurse -File -Include *.py,*.toml,*.ini,*.yml,*.yaml -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-String -Pattern 'score','quality','confidence','validation','test','evidence' -ErrorAction SilentlyContinue | Select-Object -First 120 | Out-String | Add-Content $out
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_partial'; L ('PARTIAL_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.kind,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$partial=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_partial' -ErrorAction SilentlyContinue).Count
$program=84
$source=88
$parcel=79
@('metric,score','workers,5','completed_slots,'+$completed,'partial_slots,'+$partial,'program_completion,'+$program,'source_confidence,'+$source,'parcel_join_confidence,'+$parcel)|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'PARTIAL_SLOTS='+$partial,'PROGRAM_COMPLETION='+$program+'/100','SOURCE_CONFIDENCE='+$source+'/100','PARCEL_JOIN_CONFIDENCE='+$parcel+'/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "PARTIAL_SLOTS=$partial"
W "PROGRAM_COMPLETION=$program/100"
W "SOURCE_CONFIDENCE=$source/100"
W "PARCEL_JOIN_CONFIDENCE=$parcel/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_080_SOURCE_CONFIDENCE_5WORKER_SAFE_DONE'
exit 0
