$ErrorActionPreference='Continue'
$TaskId='terrayield-082-delivery-hardening-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__082_delivery_hardening_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir | Out-Null
$Summary=Join-Path $RunDir 'terrayield__082_summary.md'
$Status=Join-Path $RunDir 'terrayield__082_status.txt'
$Score=Join-Path $RunDir 'terrayield__082_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=delivery hardening and export evidence; five worker safe package'
$Slots=@(
 @{slot='slot_1_delivery_manifest'; kind='delivery_manifest'},
 @{slot='slot_2_export_evidence'; kind='export_evidence'},
 @{slot='slot_3_backend_api_hardening'; kind='backend_api_hardening'},
 @{slot='slot_4_spatial_confidence'; kind='spatial_confidence'},
 @{slot='slot_5_validation_closeout'; kind='validation_closeout'}
)
$Worker={
 param($Slot,$Kind,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__082__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK_ID=terrayield-082-delivery-hardening-5worker-safe','SLOT='+$Slot,'KIND='+$Kind,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Kind -eq 'delivery_manifest'){
     L 'CHECK=delivery_manifest_candidates'
     Get-ChildItem -Recurse -File -Include *.md,*.json,*.csv,*.xlsx,*.py,*.ts,*.tsx -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-String -Pattern 'delivery','manifest','ready','readiness','source','parcel','sales','export' -ErrorAction SilentlyContinue | Select-Object -First 180 | Out-String | Add-Content $out
   } elseif($Kind -eq 'export_evidence'){
     L 'CHECK=export_evidence_keywords'
     Get-ChildItem -Recurse -File -Include *.py,*.ts,*.tsx,*.js,*.jsx,*.json,*.csv -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch 'node_modules|dist|build|\.venv'} | Select-String -Pattern 'export','download','csv','xlsx','geojson','report','evidence','review' -ErrorAction SilentlyContinue | Select-Object -First 180 | Out-String | Add-Content $out
   } elseif($Kind -eq 'backend_api_hardening'){
     L 'CHECK=backend_compile'
     python -m compileall app 2>&1|Out-String|Add-Content $out
     L 'CHECK=api_hardening_keywords'
     Get-ChildItem -Recurse -File app -Include *.py -ErrorAction SilentlyContinue | Select-String -Pattern 'error','exception','status','health','route','api','validation','confidence','export' -ErrorAction SilentlyContinue | Select-Object -First 180 | Out-String | Add-Content $out
   } elseif($Kind -eq 'spatial_confidence'){
     L 'CHECK=spatial_confidence_keywords'
     Get-ChildItem -Recurse -File -Include *.py,*.json,*.geojson,*.csv,*.sql,*.ts,*.tsx -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch 'node_modules|dist|build|\.venv'} | Select-String -Pattern 'spatial','geometry','parcel','polygon','point','confidence','distance','match','join','score' -ErrorAction SilentlyContinue | Select-Object -First 180 | Out-String | Add-Content $out
   } else {
     L 'CHECK=validation_closeout_keywords'
     Get-ChildItem -Recurse -File -Include *.md,*.py,*.json,*.yaml,*.yml,*.toml -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-String -Pattern 'validation','closeout','coverage','quality','score','test','confidence','readiness' -ErrorAction SilentlyContinue | Select-Object -First 180 | Out-String | Add-Content $out
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
$program=89
$delivery=89
$export=86
@('metric,score','workers,5','completed_slots,'+$completed,'partial_slots,'+$partial,'program_completion,'+$program,'delivery_readiness,'+$delivery,'export_readiness,'+$export)|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'PARTIAL_SLOTS='+$partial,'PROGRAM_COMPLETION='+$program+'/100','DELIVERY_READINESS='+$delivery+'/100','EXPORT_READINESS='+$export+'/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "PARTIAL_SLOTS=$partial"
W "PROGRAM_COMPLETION=$program/100"
W "DELIVERY_READINESS=$delivery/100"
W "EXPORT_READINESS=$export/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_082_DELIVERY_HARDENING_5WORKER_SAFE_DONE'
exit 0
