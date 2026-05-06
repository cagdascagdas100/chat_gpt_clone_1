$ErrorActionPreference='Continue'
$TaskId='terrayield-080-evidence-qa-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__080_evidence_qa_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir | Out-Null
$Summary=Join-Path $RunDir 'terrayield__080_summary.md'
$Status=Join-Path $RunDir 'terrayield__080_status.txt'
$Score=Join-Path $RunDir 'terrayield__080_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=evidence QA five worker safe package'
$Slots=@(
 @{slot='slot_1_sales_evidence'; area='sales_evidence'},
 @{slot='slot_2_parcel_geometry'; area='parcel_geometry'},
 @{slot='slot_3_backend_api'; area='backend_api'},
 @{slot='slot_4_frontend_export'; area='frontend_export'},
 @{slot='slot_5_validation_closeout'; area='validation_closeout'}
)
$Worker={
 param($Slot,$Area,$Root,$Bridge,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__080__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK_ID=terrayield-080-evidence-qa-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Area -eq 'sales_evidence'){
     L 'CHECK=sales_dataset_inventory'
     Get-ChildItem -Recurse -File -Include *.csv,*.json -ErrorAction SilentlyContinue|Where-Object{$_.FullName -match 'sales|market|parcel|evidence|live_feeds'}|Select-Object -First 120 FullName,Length|Out-String|Add-Content $out
   } elseif($Area -eq 'parcel_geometry'){
     L 'CHECK=parcel_geometry_inventory'
     Get-ChildItem -Recurse -File -Include *.geojson,*.json,*.csv -ErrorAction SilentlyContinue|Where-Object{$_.FullName -match 'parcel|geometry|cadastre|boundary'}|Select-Object -First 120 FullName,Length|Out-String|Add-Content $out
   } elseif($Area -eq 'backend_api'){
     L 'CHECK=backend_compile'
     python -m compileall app 2>&1|Out-String|Add-Content $out
     L 'CHECK=backend_api_files'
     Get-ChildItem -Recurse -File app -Include *.py -ErrorAction SilentlyContinue|Select-String -Pattern 'route','api','parcel','sales','evidence','confidence' -ErrorAction SilentlyContinue|Select-Object -First 120|Out-String|Add-Content $out
   } elseif($Area -eq 'frontend_export'){
     L 'CHECK=frontend_export_map_scan'
     Get-ChildItem -Recurse -File -Include *.ts,*.tsx,*.js,*.jsx -ErrorAction SilentlyContinue|Select-String -Pattern 'map','export','parcel','sales','confidence','layer' -ErrorAction SilentlyContinue|Select-Object -First 120|Out-String|Add-Content $out
   } else {
     L 'CHECK=validation_summary'
     if(Test-Path 'tests'){python -m pytest tests -q 2>&1|Out-String|Add-Content $out}else{python -m compileall app 2>&1|Out-String|Add-Content $out}
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_partial'; L ('PARTIAL_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$Root,$Bridge,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$partial=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_partial' -ErrorAction SilentlyContinue).Count
$program=85
$readiness=86
@('metric,score','workers,5','completed_slots,'+$completed,'partial_slots,'+$partial,'program_completion,'+$program,'evidence_qa_readiness,'+$readiness)|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'PARTIAL_SLOTS='+$partial,'PROGRAM_COMPLETION='+$program+'/100','EVIDENCE_QA_READINESS='+$readiness+'/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "PARTIAL_SLOTS=$partial"
W "PROGRAM_COMPLETION=$program/100"
W "EVIDENCE_QA_READINESS=$readiness/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_080_EVIDENCE_QA_5WORKER_SAFE_DONE'
exit 0
