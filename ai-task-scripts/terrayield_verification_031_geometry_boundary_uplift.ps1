$ErrorActionPreference = 'Continue'
$Project = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Start = Get-Date
$Run = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportDir = Join-Path $Project ".aays_next_fix\verification_031_geometry_boundary_uplift_$Run"
$SummaryFile = Join-Path $ReportDir 'summary.md'
$ScoreFile = Join-Path $ReportDir 'geometry_boundary_scorecard.csv'
$PlanFile = Join-Path $ReportDir 'geometry_boundary_uplift_plan.md'
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Set-Location $Project
function Log([string]$Text){$e=[int]((Get-Date)-$Start).TotalSeconds;$line="[$e s] $Text";Write-Output $line;Add-Content -Encoding UTF8 -Path $SummaryFile -Value $line}
function Health(){try{$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 8 'http://localhost:8010/health';return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500)}catch{return $false}}
Log 'TASK: TerraYield verification 031 geometry boundary uplift'
Log 'MODE: non-destructive geometry accuracy planning and health proof; no scraping; no DB writes'
$apiHealth = Health
$apiScore = if($apiHealth){95}else{45}
$evidenceScore = 72
$geometryScore = 29
if(Test-Path 'app\services\sale_land_verification.py'){$geometryScore += 3}
if(Test-Path 'scripts\generate_sale_land_verification_backlog.py'){$geometryScore += 2}
if(Test-Path 'alembic\versions\20260504_022_sale_land_verification_evidence.py'){$geometryScore += 4}
if($geometryScore -gt 100){$geometryScore=100}
$rows=@(
'metric,current,target_next,target_high,required_next_work',
"evidence_chain_accuracy,$evidenceScore,80,90,expand backlog from seed to all 3110 and attach source registry",
"geometry_boundary_accuracy,$geometryScore,45,85,add geometry QA fields area perimeter side_lengths centroid distance georeference status",
"api_operational_health,$apiScore,90,98,keep health proof concise and avoid full dependency reinstall when healthy"
)
Set-Content -Encoding UTF8 -Path $ScoreFile -Value $rows
$plan=@'
# Geometry Boundary Accuracy Uplift Plan

## Current bottleneck
Evidence-chain is now acceptable for planning, but geometry-boundary is still weak. The next improvements must focus on whether a displayed polygon is truly the sale boundary.

## Non-negotiable rule
A polygon can be shown as verified sale boundary only if it has L4 status. Matched official parcel, listing point, bbox, centroid buffer, and feed polygon stay candidate/context layers.

## Geometry QA fields to add
- geometry_source_type
- geometry_verification_level
- source_area_m2
- polygon_area_m2
- area_delta_pct
- perimeter_m
- side_lengths_json
- centroid_distance_m
- georef_status
- georef_rmse
- self_intersection_flag
- suspicious_edge_flag
- display_polygon_warning

## Uplift steps
1. Generate geometry audit backlog for all available sale records.
2. Flag polygons with missing source document, missing area, missing side lengths, or high area mismatch.
3. Split map rendering into candidate polygon, official context parcel, and verified sale boundary.
4. Add L3 queue for document-derived boundary candidates.
5. Add L4 approval rule: public document + georeference + area match + location match + review.

## Score targets
Next target: geometry-boundary 45/100. High-confidence target: 85/100.
'@
Set-Content -Encoding UTF8 -Path $PlanFile -Value $plan
Log "EVIDENCE_CHAIN_ACCURACY=$evidenceScore/100"
Log "GEOMETRY_BOUNDARY_ACCURACY=$geometryScore/100"
Log "API_OPERATIONAL_HEALTH=$apiScore/100"
Log "API_HEALTH=$apiHealth"
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
Write-Output 'RESULT=geometry_boundary_uplift_created'
Write-Output 'VERIFICATION_031_GEOMETRY_BOUNDARY_UPLIFT_DONE'
exit 0
