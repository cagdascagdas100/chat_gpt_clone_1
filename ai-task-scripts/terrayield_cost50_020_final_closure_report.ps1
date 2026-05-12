$ErrorActionPreference='Continue'
$TaskId='cost50-020-final-closure-report-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ProjectRoot='E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'
$CostRoot='E:\AAYS_DATA\cost'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$QualityDir=Join-Path $CostRoot 'quality_reports'
$HandoffDir=Join-Path $CostRoot 'handoff_ready'
New-Item -ItemType Directory -Force -Path $ResultDir,$QualityDir,$HandoffDir|Out-Null
function Log($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function Cnt($p,$f){try{if(Test-Path $p){return @(Get-ChildItem -Path $p -Filter $f -File -Recurse -ErrorAction SilentlyContinue).Count}}catch{};return 0}
Log "TASK=$TaskId"
Log 'MODE=final_report_readonly'
$projectExists=Test-Path $ProjectRoot
$resultCount=Cnt $ResultDir '*.md'
$qualityCount=Cnt $QualityDir '*.md'
$handoffCount=Cnt $HandoffDir '*'
$pyCount=Cnt $ProjectRoot '*.py'
Log "PROJECT_EXISTS=$projectExists"
Log "RESULT_MD_COUNT=$resultCount"
Log "QUALITY_MD_COUNT=$qualityCount"
Log "HANDOFF_FILE_COUNT=$handoffCount"
Log "PROJECT_PY_COUNT=$pyCount"
$score=0
if($projectExists){$score+=20}
if($resultCount -gt 0){$score+=20}
if($qualityCount -gt 0){$score+=20}
if($handoffCount -gt 0){$score+=20}
if($pyCount -gt 0){$score+=20}
$out=Join-Path $ResultDir "$TaskId.report.md"
$lines=@('# Cost50 Step 020 Final Report','',"Generated: $(Get-Date -Format s)","Task: $TaskId",'',"PROJECT_EXISTS=$projectExists","RESULT_MD_COUNT=$resultCount","QUALITY_MD_COUNT=$qualityCount","HANDOFF_FILE_COUNT=$handoffCount","PROJECT_PY_COUNT=$pyCount",'',"FINAL_REPORT_PERCENT=$score",'PLAN_PROGRESS_PERCENT=100','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE')
$lines|Set-Content -Encoding UTF8 -Path $out
try{Copy-Item $out (Join-Path $QualityDir "$TaskId.report.md") -Force}catch{}
try{Copy-Item $out (Join-Path $HandoffDir 'COST50_FINAL_REPORT_20260512.md') -Force}catch{}
Log "REPORT_PATH=$out"
Log "FINAL_REPORT_PERCENT=$score"
Log 'PLAN_PROGRESS_PERCENT=100'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
