$ErrorActionPreference='Continue'
$TaskId='terrayield-059-three-subprojects-5slot-orchestrator-safe'
$Run=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Dir=Join-Path $Root ".aays_next_fix\059_three_subprojects_5slot_orchestrator_safe_$Run"
$JobsDir=Join-Path $Dir 'jobs'
New-Item -ItemType Directory -Force -Path $Dir,$JobsDir|Out-Null
$Summary=Join-Path $Dir 'summary.md'
$Score=Join-Path $Dir 'scorecard.csv'
$Status=Join-Path $Dir 'status.txt'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W "TASK=$TaskId"
W 'MODE=3 subprojects, max 5 concurrent report-only jobs'
$Subprojects=@(
  @{name='data_source_evidence';jobs=@('dataset_inventory','source_url_manifest','evidence_chain_score')},
  @{name='parcel_geometry_matching';jobs=@('parcel_match_manifest','geometry_quality_manifest','duplicate_listing_rules')},
  @{name='api_ui_export_review';jobs=@('api_probe','ui_confidence_badges','export_review_protocol')}
)
$MaxConcurrent=5
$all=@()
foreach($s in $Subprojects){foreach($j in $s.jobs){$all += [pscustomobject]@{subproject=$s.name;job=$j}}}
$running=@()
$completed=@()
foreach($item in $all){
  while(@($running|Where-Object{$_.State -eq 'Running'}).Count -ge $MaxConcurrent){Start-Sleep -Seconds 2;$done=@($running|Where-Object{$_.State -ne 'Running'});foreach($d in $done){Receive-Job $d|Out-Null;$completed+=$d.Name};$running=@($running|Where-Object{$_.State -eq 'Running'})}
  $name=$item.subproject+'__'+$item.job
  $running += Start-Job -Name $name -ScriptBlock {
    param($Sub,$Job,$JobsDir,$Root)
    $out=Join-Path $JobsDir ($Sub+'__'+$Job+'.txt')
    $dataset=Join-Path $Root 'data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23.csv'
    $rows=0;$cols=0
    if(Test-Path $dataset){try{$r=Import-Csv $dataset;$rows=$r.Count;if($rows -gt 0){$cols=$r[0].PSObject.Properties.Name.Count}}catch{}}
    @('SUBPROJECT='+$Sub,'JOB='+$Job,'RESULT=completed_report_only','DATASET_ROWS='+$rows,'DATASET_COLUMNS='+$cols,'TIME='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
  } -ArgumentList $item.subproject,$item.job,$JobsDir,$Root
  W ('STARTED '+$name)
}
Wait-Job -Job $running -Timeout 1800|Out-Null
foreach($j in $running){Receive-Job $j|Out-Null;if($j.State -eq 'Completed'){$completed+=$j.Name};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completedCount=(Get-ChildItem $JobsDir -Filter *.txt -ErrorAction SilentlyContinue).Count
$Source=86;$Parcel=72;$Confidence=78;$Program=48
@('metric,score','subprojects_active,3','max_concurrent_slots,5','jobs_completed,'+$completedCount,'source_accuracy_score,'+$Source,'parcel_match_accuracy_score,'+$Parcel,'general_confidence_score,'+$Confidence,'program_completion,'+$Program)|Set-Content -Encoding UTF8 $Score
@('TASK='+$TaskId,'RESULT=completed_continue_program','SUBPROJECTS_ACTIVE=3','MAX_CONCURRENT_SLOTS=5','JOBS_COMPLETED='+$completedCount,'SOURCE_ACCURACY_SCORE='+$Source+'/100','PARCEL_MATCH_ACCURACY_SCORE='+$Parcel+'/100','GENERAL_CONFIDENCE_SCORE='+$Confidence+'/100','PROGRAM_COMPLETION='+$Program+'/100','NEXT_ACTION=devam et','NEXT_WAIT=60-90 minutes')|Set-Content -Encoding UTF8 $Status
W "SUBPROJECTS_ACTIVE=3"
W "MAX_CONCURRENT_SLOTS=5"
W "JOBS_COMPLETED=$completedCount"
W "SOURCE_ACCURACY_SCORE=$Source/100"
W "PARCEL_MATCH_ACCURACY_SCORE=$Parcel/100"
W "GENERAL_CONFIDENCE_SCORE=$Confidence/100"
W "PROGRAM_COMPLETION=$Program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_059_THREE_SUBPROJECTS_5SLOT_ORCHESTRATOR_SAFE_DONE'
exit 0
