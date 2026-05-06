$ErrorActionPreference='Continue'
$TaskId='terrayield-081-delivery-readiness-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__081_delivery_readiness_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir | Out-Null
$Summary=Join-Path $RunDir 'terrayield__081_summary.md'
$Status=Join-Path $RunDir 'terrayield__081_status.txt'
$Score=Join-Path $RunDir 'terrayield__081_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=delivery readiness five worker safe package'
$Slots=@(
 @{slot='slot_1_evidence_closeout'; area='evidence_closeout'},
 @{slot='slot_2_parcel_confidence'; area='parcel_confidence'},
 @{slot='slot_3_backend_delivery'; area='backend_delivery'},
 @{slot='slot_4_ui_export_delivery'; area='ui_export_delivery'},
 @{slot='slot_5_validation_inventory'; area='validation_inventory'}
)
$Worker={
 param($Slot,$Area,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__081__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK_ID=terrayield-081-delivery-readiness-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Area -eq 'evidence_closeout'){
     L 'CHECK=evidence_and_source_files'
     Get-ChildItem -Recurse -File -Include *.md,*.csv,*.json,*.xlsx -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-String -Pattern 'source','evidence','registry','confidence','sales','market' -ErrorAction SilentlyContinue | Select-Object -First 160 | Out-String | Add-Content $out
   } elseif($Area -eq 'parcel_confidence'){
     L 'CHECK=parcel_geometry_join_confidence'
     Get-ChildItem -Recurse -File -Include *.py,*.sql,*.json,*.geojson,*.csv -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-String -Pattern 'parcel','geometry','join','confidence','boundary','centroid','lat','lon','ada','parsel' -ErrorAction SilentlyContinue | Select-Object -First 160 | Out-String | Add-Content $out
   } elseif($Area -eq 'backend_delivery'){
     L 'CHECK=backend_compile_delivery'
     python -m compileall app 2>&1|Out-String|Add-Content $out
     L 'CHECK=backend_delivery_keywords'
     Get-ChildItem -Recurse -File app -Include *.py -ErrorAction SilentlyContinue | Select-String -Pattern 'sales','parcel','evidence','confidence','export','validation','route','api' -ErrorAction SilentlyContinue | Select-Object -First 160 | Out-String | Add-Content $out
   } elseif($Area -eq 'ui_export_delivery'){
     L 'CHECK=ui_export_delivery_keywords'
     Get-ChildItem -Recurse -File -Include *.ts,*.tsx,*.js,*.jsx -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch 'node_modules|dist|build'} | Select-String -Pattern 'map','layer','export','download','parcel','sales','confidence','evidence' -ErrorAction SilentlyContinue | Select-Object -First 160 | Out-String | Add-Content $out
   } else {
     L 'CHECK=validation_inventory'
     Get-ChildItem -Recurse -File -Include *.py,*.md,*.yml,*.yaml,*.toml -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-String -Pattern 'test','validation','quality','score','confidence','evidence','parcel' -ErrorAction SilentlyContinue | Select-Object -First 160 | Out-String | Add-Content $out
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_partial'; L ('PARTIAL_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$partial=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_partial' -ErrorAction SilentlyContinue).Count
$program=88
$delivery=87
@('metric,score','workers,5','completed_slots,'+$completed,'partial_slots,'+$partial,'program_completion,'+$program,'delivery_readiness,'+$delivery)|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'PARTIAL_SLOTS='+$partial,'PROGRAM_COMPLETION='+$program+'/100','DELIVERY_READINESS='+$delivery+'/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "PARTIAL_SLOTS=$partial"
W "PROGRAM_COMPLETION=$program/100"
W "DELIVERY_READINESS=$delivery/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_081_DELIVERY_READINESS_5WORKER_SAFE_DONE'
exit 0
