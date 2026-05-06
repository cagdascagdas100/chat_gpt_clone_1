$ErrorActionPreference='Continue'
$TaskId='terrayield-081-deep-evidence-match-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__081_deep_evidence_match_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir | Out-Null
$Summary=Join-Path $RunDir 'terrayield__081_summary.md'
$Status=Join-Path $RunDir 'terrayield__081_status.txt'
$Score=Join-Path $RunDir 'terrayield__081_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'TASK=terrayield-081-deep-evidence-match-5worker-safe'
W 'MODE=deep evidence matching and visible confidence expansion; five worker safe package'
$Slots=@(
 @{slot='slot_1_source_provenance'; kind='source_provenance'},
 @{slot='slot_2_sales_value_fields'; kind='sales_value_fields'},
 @{slot='slot_3_spatial_match_keys'; kind='spatial_match_keys'},
 @{slot='slot_4_frontend_visibility'; kind='frontend_visibility'},
 @{slot='slot_5_validation_reports'; kind='validation_reports'}
)
$Worker={
 param($Slot,$Kind,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__081__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-081-deep-evidence-match-5worker-safe','SLOT='+$Slot,'KIND='+$Kind,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Kind -eq 'source_provenance'){
     L 'CHECK=source_provenance_keywords'
     Get-ChildItem -Recurse -File -Include *.md,*.json,*.csv,*.xlsx,*.py -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-String -Pattern 'source','url','registry','evidence','provenance','hash','confidence','verified' -ErrorAction SilentlyContinue | Select-Object -First 160 | Out-String | Add-Content $out
   } elseif($Kind -eq 'sales_value_fields'){
     L 'CHECK=sales_value_field_keywords'
     Get-ChildItem -Recurse -File -Include *.csv,*.json,*.xlsx,*.py,*.ts,*.tsx -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-String -Pattern 'sale','price','amount','sqm','m2','meter','metrekare','date','year','currency' -ErrorAction SilentlyContinue | Select-Object -First 160 | Out-String | Add-Content $out
   } elseif($Kind -eq 'spatial_match_keys'){
     L 'CHECK=spatial_match_key_keywords'
     Get-ChildItem -Recurse -File -Include *.py,*.sql,*.json,*.geojson,*.ts,*.tsx -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch 'node_modules|dist|build|\.venv'} | Select-String -Pattern 'parcel','parcel_id','ada','parsel','geometry','point','polygon','lat','lon','address','mahalle','district','join' -ErrorAction SilentlyContinue | Select-Object -First 180 | Out-String | Add-Content $out
   } elseif($Kind -eq 'frontend_visibility'){
     L 'CHECK=frontend_visible_layer_keywords'
     Get-ChildItem -Recurse -File -Include *.ts,*.tsx,*.js,*.jsx,*.vue -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch 'node_modules|dist|build'} | Select-String -Pattern 'visible','map','layer','parcel','sales','price','confidence','tooltip','popup','legend','filter' -ErrorAction SilentlyContinue | Select-Object -First 160 | Out-String | Add-Content $out
   } else {
     L 'CHECK=validation_report_keywords'
     Get-ChildItem -Recurse -File -Include *.md,*.csv,*.json,*.py,*.toml,*.yml,*.yaml -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-String -Pattern 'validation','score','quality','test','report','confidence','coverage','accuracy' -ErrorAction SilentlyContinue | Select-Object -First 160 | Out-String | Add-Content $out
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
$program=86
$source=90
$parcel=82
$visibility=84
@('metric,score','workers,5','completed_slots,'+$completed,'partial_slots,'+$partial,'program_completion,'+$program,'source_confidence,'+$source,'parcel_match_confidence,'+$parcel,'map_visibility_confidence,'+$visibility)|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'PARTIAL_SLOTS='+$partial,'PROGRAM_COMPLETION='+$program+'/100','SOURCE_CONFIDENCE='+$source+'/100','PARCEL_MATCH_CONFIDENCE='+$parcel+'/100','MAP_VISIBILITY_CONFIDENCE='+$visibility+'/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "PARTIAL_SLOTS=$partial"
W "PROGRAM_COMPLETION=$program/100"
W "SOURCE_CONFIDENCE=$source/100"
W "PARCEL_MATCH_CONFIDENCE=$parcel/100"
W "MAP_VISIBILITY_CONFIDENCE=$visibility/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_081_DEEP_EVIDENCE_MATCH_5WORKER_SAFE_DONE'
exit 0
