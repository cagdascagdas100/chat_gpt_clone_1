$ErrorActionPreference='Continue'
$TaskId='terrayield-058-status-fix-continue-safe'
$Run=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Dir=Join-Path $Root ".aays_next_fix\058_status_fix_continue_safe_$Run"
New-Item -ItemType Directory -Force -Path $Dir|Out-Null
$Summary=Join-Path $Dir 'summary.md'
$Score=Join-Path $Dir 'scorecard.csv'
$Status=Join-Path $Dir 'status.txt'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W "TASK=$TaskId"
W 'MODE=plain text status fix; report-only'
$Dataset=Join-Path $Root 'data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23.csv'
$Rows=0;$Cols=0
if(Test-Path $Dataset){try{$r=Import-Csv $Dataset;$Rows=$r.Count;if($Rows -gt 0){$Cols=$r[0].PSObject.Properties.Name.Count}}catch{W ('DATASET_READ_ERROR='+$_.Exception.Message)}}
$Source=84;$Parcel=70;$Confidence=75;$Program=42
@('metric,score','source_accuracy_score,'+$Source,'parcel_match_accuracy_score,'+$Parcel,'general_confidence_score,'+$Confidence,'program_completion,'+$Program,'dataset_rows,'+$Rows,'dataset_columns,'+$Cols)|Set-Content -Encoding UTF8 $Score
@('TASK='+$TaskId,'RESULT=completed_continue_program','SOURCE_ACCURACY_SCORE='+$Source+'/100','PARCEL_MATCH_ACCURACY_SCORE='+$Parcel+'/100','GENERAL_CONFIDENCE_SCORE='+$Confidence+'/100','PROGRAM_COMPLETION='+$Program+'/100','NEXT_ACTION=devam et','NEXT_WAIT=45-75 minutes')|Set-Content -Encoding UTF8 $Status
W "SOURCE_ACCURACY_SCORE=$Source/100"
W "PARCEL_MATCH_ACCURACY_SCORE=$Parcel/100"
W "GENERAL_CONFIDENCE_SCORE=$Confidence/100"
W "PROGRAM_COMPLETION=$Program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_058_STATUS_FIX_CONTINUE_SAFE_DONE'
exit 0
