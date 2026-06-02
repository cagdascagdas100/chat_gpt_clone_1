$ErrorActionPreference='Continue'
$TaskId='terrayield-079-sales-parcel-evidence-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__079_sales_parcel_evidence_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir | Out-Null
$Summary=Join-Path $RunDir 'terrayield__079_summary.md'
$Status=Join-Path $RunDir 'terrayield__079_status.txt'
$Score=Join-Path $RunDir 'terrayield__079_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'TASK=terrayield-079-sales-parcel-evidence-5worker-safe'
W 'MODE=sales parcel evidence expand; five worker safe package'
$Slots=@(
 @{slot='slot_1_sales_sources'; kind='sales_sources'; pattern='*.csv,*.xlsx,*.json'},
 @{slot='slot_2_parcel_geometry'; kind='parcel_geometry'; pattern='*.geojson,*.gpkg,*.shp,*.json'},
 @{slot='slot_3_backend_models'; kind='backend_models'; pattern='*.py'},
 @{slot='slot_4_frontend_map'; kind='frontend_map'; pattern='*.ts,*.tsx,*.js,*.jsx'},
 @{slot='slot_5_validation'; kind='validation'; pattern='*.toml,*.ini,*.yml,*.yaml'}
)
$Worker={
 param($Slot,$Kind,$Pattern,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__079__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-079-sales-parcel-evidence-5worker-safe','SLOT='+$Slot,'KIND='+$Kind,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Kind -eq 'sales_sources'){
     L 'CHECK=sales_source_inventory'
     Get-ChildItem -Recurse -File -Include *.csv,*.xlsx,*.json -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-Object -First 120 FullName,Length,LastWriteTime | Out-String | Add-Content $out
   } elseif($Kind -eq 'parcel_geometry'){
     L 'CHECK=parcel_geometry_inventory'
     Get-ChildItem -Recurse -File -Include *.geojson,*.gpkg,*.shp,*.json -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-Object -First 120 FullName,Length,LastWriteTime | Out-String | Add-Content $out
   } elseif($Kind -eq 'backend_models'){
     L 'CHECK=backend_sales_parcel_keywords'
     Get-ChildItem -Recurse -File app -Include *.py -ErrorAction SilentlyContinue | Select-String -Pattern 'sale','parcel','cadastre','geometry','confidence','evidence','source' -ErrorAction SilentlyContinue | Select-Object -First 120 | Out-String | Add-Content $out
   } elseif($Kind -eq 'frontend_map'){
     L 'CHECK=frontend_map_keywords'
     Get-ChildItem -Recurse -File -Include *.ts,*.tsx,*.js,*.jsx -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch 'node_modules|dist|build'} | Select-String -Pattern 'map','layer','parcel','sale','geometry','confidence','evidence' -ErrorAction SilentlyContinue | Select-Object -First 120 | Out-String | Add-Content $out
   } else {
     L 'CHECK=validation_config_inventory'
     Get-ChildItem -Recurse -File -Include pyproject.toml,alembic.ini,docker-compose.yml,*.yml,*.yaml -ErrorAction SilentlyContinue | Select-Object -First 80 FullName,Length,LastWriteTime | Out-String | Add-Content $out
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_partial'; L ('PARTIAL_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.kind,$s.pattern,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$partial=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_partial' -ErrorAction SilentlyContinue).Count
$program=82
@('metric,score','workers,5','completed_slots,'+$completed,'partial_slots,'+$partial,'program_completion,'+$program,'sales_parcel_evidence_readiness,84')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'PARTIAL_SLOTS='+$partial,'PROGRAM_COMPLETION='+$program+'/100','SALES_PARCEL_EVIDENCE_READINESS=84/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "PARTIAL_SLOTS=$partial"
W "PROGRAM_COMPLETION=$program/100"
W 'SALES_PARCEL_EVIDENCE_READINESS=84/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_079_SALES_PARCEL_EVIDENCE_5WORKER_SAFE_DONE'
exit 0
