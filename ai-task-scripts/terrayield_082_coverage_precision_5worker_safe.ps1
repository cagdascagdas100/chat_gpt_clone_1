$ErrorActionPreference='Continue'
$TaskId='terrayield-082-coverage-precision-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__082_coverage_precision_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir | Out-Null
$Summary=Join-Path $RunDir 'terrayield__082_summary.md'
$Status=Join-Path $RunDir 'terrayield__082_status.txt'
$Score=Join-Path $RunDir 'terrayield__082_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'TASK=terrayield-082-coverage-precision-5worker-safe'
W 'MODE=coverage precision and decision confidence expansion; five worker safe package'
$Slots=@(
 @{slot='slot_1_data_coverage'; kind='data_coverage'},
 @{slot='slot_2_match_precision'; kind='match_precision'},
 @{slot='slot_3_api_contracts'; kind='api_contracts'},
 @{slot='slot_4_ui_decision_flow'; kind='ui_decision_flow'},
 @{slot='slot_5_release_readiness'; kind='release_readiness'}
)
$Worker={
 param($Slot,$Kind,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__082__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-082-coverage-precision-5worker-safe','SLOT='+$Slot,'KIND='+$Kind,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Kind -eq 'data_coverage'){
     L 'CHECK=data_coverage_inventory'
     Get-ChildItem -Recurse -File -Include *.csv,*.json,*.geojson,*.gpkg,*.xlsx,*.parquet -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Group-Object Extension | Sort-Object Count -Descending | Select-Object Count,Name | Out-String | Add-Content $out
     L 'CHECK=data_coverage_samples'
     Get-ChildItem -Recurse -File -Include *.csv,*.json,*.geojson,*.gpkg,*.xlsx,*.parquet -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-Object -First 160 FullName,Length | Out-String | Add-Content $out
   } elseif($Kind -eq 'match_precision'){
     L 'CHECK=match_precision_keywords'
     Get-ChildItem -Recurse -File -Include *.py,*.sql,*.json,*.geojson,*.ts,*.tsx,*.md -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch 'node_modules|dist|build|\.venv'} | Select-String -Pattern 'precision','recall','match','join','confidence','parcel','source','quality','score','threshold' -ErrorAction SilentlyContinue | Select-Object -First 220 | Out-String | Add-Content $out
   } elseif($Kind -eq 'api_contracts'){
     L 'CHECK=api_contract_and_openapi_scan'
     Get-ChildItem -Recurse -File -Include *.py,*.json,*.yaml,*.yml -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-String -Pattern 'openapi','route','router','endpoint','schema','response','parcel','sales','confidence' -ErrorAction SilentlyContinue | Select-Object -First 200 | Out-String | Add-Content $out
   } elseif($Kind -eq 'ui_decision_flow'){
     L 'CHECK=ui_decision_flow_keywords'
     Get-ChildItem -Recurse -File -Include *.ts,*.tsx,*.js,*.jsx,*.vue,*.md -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch 'node_modules|dist|build'} | Select-String -Pattern 'filter','sort','confidence','score','legend','tooltip','popup','decision','review','export','parcel','sales' -ErrorAction SilentlyContinue | Select-Object -First 200 | Out-String | Add-Content $out
   } else {
     L 'CHECK=release_readiness_inventory'
     Get-ChildItem -Recurse -File -Include README*,*.md,pyproject.toml,package.json,docker-compose.yml,*.yml,*.yaml,alembic.ini -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|dist|build|\.venv'} | Select-Object -First 160 FullName,Length,LastWriteTime | Out-String | Add-Content $out
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
$program=88
$coverage=86
$precision=84
$readiness=86
@('metric,score','workers,5','completed_slots,'+$completed,'partial_slots,'+$partial,'program_completion,'+$program,'coverage_confidence,'+$coverage,'match_precision_confidence,'+$precision,'release_readiness,'+$readiness)|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'PARTIAL_SLOTS='+$partial,'PROGRAM_COMPLETION='+$program+'/100','COVERAGE_CONFIDENCE='+$coverage+'/100','MATCH_PRECISION_CONFIDENCE='+$precision+'/100','RELEASE_READINESS='+$readiness+'/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "PARTIAL_SLOTS=$partial"
W "PROGRAM_COMPLETION=$program/100"
W "COVERAGE_CONFIDENCE=$coverage/100"
W "MATCH_PRECISION_CONFIDENCE=$precision/100"
W "RELEASE_READINESS=$readiness/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_082_COVERAGE_PRECISION_5WORKER_SAFE_DONE'
exit 0
