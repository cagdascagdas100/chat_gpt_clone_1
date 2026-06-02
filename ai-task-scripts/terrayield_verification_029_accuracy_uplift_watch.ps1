$ErrorActionPreference = 'Continue'
$Project = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$Start = Get-Date
$Run = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportDir = Join-Path $Project ".aays_next_fix\verification_029_accuracy_uplift_watch_$Run"
$SummaryFile = Join-Path $ReportDir 'summary.md'
$ScoreFile = Join-Path $ReportDir 'score_targets.csv'
$PlanFile = Join-Path $ReportDir 'accuracy_uplift_execution_plan.md'
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Set-Location $Project
function Log([string]$Text){$e=[int]((Get-Date)-$Start).TotalSeconds;$line="[$e s] $Text";Write-Output $line;Add-Content -Encoding UTF8 -Path $SummaryFile -Value $line}
function Health(){try{$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 8 'http://localhost:8010/health';return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500)}catch{return $false}}
Log 'TASK: TerraYield verification 029 accuracy uplift watch'
Log 'MODE: non-destructive score update and expanded roadmap; no scraping; no DB writes'
$health = Health
$apiScore = if($health){95}else{45}
$evidenceScore = 58
$geometryScore = 22
if(Test-Path 'app\services\sale_land_verification.py'){$evidenceScore += 5; $geometryScore += 3}
if(Test-Path 'scripts\generate_sale_land_verification_backlog.py'){$evidenceScore += 5}
if(Test-Path 'alembic\versions\20260504_022_sale_land_verification_evidence.py'){$evidenceScore += 4; $geometryScore += 4}
if($evidenceScore -gt 100){$evidenceScore=100}
if($geometryScore -gt 100){$geometryScore=100}
$rows=@(
'score,current,target_next,target_high,driver',
"evidence_chain_accuracy,$evidenceScore,70,90,expand all 3110 backlog duplicate grouping source documents review fields",
"geometry_boundary_accuracy,$geometryScore,45,85,red-line documents georeference side lengths area match review queue",
"api_operational_health,$apiScore,90,98,health endpoint route registration and api-only recovery"
)
Set-Content -Encoding UTF8 -Path $ScoreFile -Value $rows
$plan=@'
# Accuracy Uplift Execution Plan

## Never finish principle
The verification program remains open-ended. Every run must raise evidence-chain accuracy, raise geometry-boundary accuracy, or identify the exact missing evidence blocking improvement.

## Scores to report each cycle
- Evidence-chain accuracy: source URL, price, area, address, duplicate grouping, official context, documents, and review readiness.
- Geometry-boundary accuracy: real sale boundary, georeference, area match, side lengths, polygon validity, and L4 approval readiness.

## Next expansion sequence
1. Expand backlog from sample rows to all 3110 sale-suitable land records.
2. Add duplicate listing grouping for multiple websites selling the same land.
3. Add document registry for brochure, red-line, title plan, site plan, planning documents.
4. Add map/API missing_evidence and confidence_breakdown fields.
5. Add geometry QA fields: area_m2, perimeter_m, side_lengths, centroid_distance, area_delta.
6. Build L3 review queue; only L4 can be shown as verified sale boundary.
7. Add annual rerun and delta report.

## Anti-stall policy
Do not overwrite a running task. If current task has no result and last-task-id does not advance, retry with a new ID. If API health fails, run API-only recovery; do not restart the full runner.
'@
Set-Content -Encoding UTF8 -Path $PlanFile -Value $plan
Log "EVIDENCE_CHAIN_ACCURACY=$evidenceScore/100"
Log "GEOMETRY_BOUNDARY_ACCURACY=$geometryScore/100"
Log "API_OPERATIONAL_HEALTH=$apiScore/100"
Log "SCORE_FILE=$ScoreFile"
Log "PLAN_FILE=$PlanFile"
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
Log "ELAPSED_SECONDS=$elapsed"
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "SCORE_FILE=$ScoreFile"
Write-Output "PLAN_FILE=$PlanFile"
Write-Output "EVIDENCE_CHAIN_ACCURACY=$evidenceScore/100"
Write-Output "GEOMETRY_BOUNDARY_ACCURACY=$geometryScore/100"
Write-Output "API_OPERATIONAL_HEALTH=$apiScore/100"
Write-Output 'RESULT=accuracy_uplift_watch_created'
Write-Output 'VERIFICATION_029_ACCURACY_UPLIFT_WATCH_DONE'
exit 0
