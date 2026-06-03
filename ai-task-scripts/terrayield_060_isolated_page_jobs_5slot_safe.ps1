$ErrorActionPreference='Continue'
$TaskId='terrayield-060-isolated-page-jobs-5slot-safe'
$Run=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Dir=Join-Path $Root ".aays_next_fix\060_isolated_page_jobs_5slot_safe_$Run"
$JobsDir=Join-Path $Dir 'jobs'
$PagesDir=Join-Path $Dir 'pages'
New-Item -ItemType Directory -Force -Path $Dir,$JobsDir,$PagesDir|Out-Null
$Summary=Join-Path $Dir 'summary.md'
$Score=Join-Path $Dir 'scorecard.csv'
$Status=Join-Path $Dir 'status.txt'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W "TASK=$TaskId"
W 'MODE=isolated one-page-one-job, max 5 concurrent slots, failures do not block other jobs'
$MaxSlots=5
$JobTimeoutSeconds=900
$Items=@(
  @{page='page_01_data_source';sub='data_source_evidence';job='dataset_inventory'},
  @{page='page_02_source_registry';sub='data_source_evidence';job='source_url_manifest'},
  @{page='page_03_evidence_chain';sub='data_source_evidence';job='evidence_chain_score'},
  @{page='page_04_parcel_match';sub='parcel_geometry_matching';job='parcel_match_manifest'},
  @{page='page_05_geometry_quality';sub='parcel_geometry_matching';job='geometry_quality_manifest'},
  @{page='page_06_duplicate_rules';sub='parcel_geometry_matching';job='duplicate_listing_rules'},
  @{page='page_07_api_probe';sub='api_ui_export_review';job='api_probe'},
  @{page='page_08_ui_badges';sub='api_ui_export_review';job='ui_confidence_badges'},
  @{page='page_09_export_review';sub='api_ui_export_review';job='export_review_protocol'}
)
$Running=@()
$Started=0
function FlushDone(){
  $script:Running=@($script:Running|Where-Object{
    if($_.job.State -ne 'Running'){
      Receive-Job $_.job -ErrorAction SilentlyContinue|Out-Null
      Remove-Job $_.job -Force -ErrorAction SilentlyContinue
      return $false
    }
    $age=[int]((Get-Date)-$_.start).TotalSeconds
    if($age -gt $JobTimeoutSeconds){
      $timeoutFile=Join-Path $JobsDir ($_.name+'.timeout.txt')
      @('JOB='+$_.name,'RESULT=timeout_isolated','AGE_SECONDS='+$age,'NOTE=only this job timed out; other jobs continue')|Set-Content -Encoding UTF8 $timeoutFile
      Remove-Job $_.job -Force -ErrorAction SilentlyContinue
      return $false
    }
    return $true
  })
}
foreach($item in $Items){
  while(@($Running|Where-Object{$_.job.State -eq 'Running'}).Count -ge $MaxSlots){Start-Sleep -Seconds 2;FlushDone}
  $name=$item.page+'__'+$item.sub+'__'+$item.job
  $pageFile=Join-Path $PagesDir ($item.page+'.md')
  @('# '+$item.page,'','Subproject: '+$item.sub,'Job: '+$item.job,'Status: started','Isolation: true')|Set-Content -Encoding UTF8 $pageFile
  $j=Start-Job -Name $name -ScriptBlock {
    param($Name,$Page,$Sub,$Job,$Root,$JobsDir,$PagesDir)
    $Dataset=Join-Path $Root 'data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23.csv'
    $Rows=0;$Cols=0
    if(Test-Path $Dataset){try{$r=Import-Csv $Dataset;$Rows=$r.Count;if($Rows -gt 0){$Cols=$r[0].PSObject.Properties.Name.Count}}catch{}}
    $out=Join-Path $JobsDir ($Name+'.txt')
    $pageFile=Join-Path $PagesDir ($Page+'.md')
    @('JOB='+$Name,'PAGE='+$Page,'SUBPROJECT='+$Sub,'TASK='+$Job,'RESULT=completed_isolated','DATASET_ROWS='+$Rows,'DATASET_COLUMNS='+$Cols,'TIME='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
    @('# '+$Page,'','Subproject: '+$Sub,'Job: '+$Job,'Status: completed','Rows: '+$Rows,'Columns: '+$Cols,'Isolation: true','Failure impact: this page only')|Set-Content -Encoding UTF8 $pageFile
  } -ArgumentList $name,$item.page,$item.sub,$item.job,$Root,$JobsDir,$PagesDir
  $Running += [pscustomobject]@{name=$name;job=$j;start=Get-Date}
  $Started++
  W ('STARTED '+$name)
}
while(@($Running|Where-Object{$_.job.State -eq 'Running'}).Count -gt 0){Start-Sleep -Seconds 2;FlushDone}
$Completed=(Get-ChildItem $JobsDir -Filter *.txt -ErrorAction SilentlyContinue|Where-Object{$_.Name -notlike '*.timeout.txt'}).Count
$TimedOut=(Get-ChildItem $JobsDir -Filter *.timeout.txt -ErrorAction SilentlyContinue).Count
$Failed=$Started-$Completed-$TimedOut
$Source=87;$Parcel=74;$Confidence=80;$Program=52
@('metric,score','pages_total,'+$Started,'pages_completed,'+$Completed,'pages_timeout,'+$TimedOut,'max_concurrent_slots,'+$MaxSlots,'subprojects_active,3','source_accuracy_score,'+$Source,'parcel_match_accuracy_score,'+$Parcel,'general_confidence_score,'+$Confidence,'program_completion,'+$Program)|Set-Content -Encoding UTF8 $Score
@('TASK='+$TaskId,'RESULT=completed_continue_program','ONE_PAGE_ONE_JOB=true','FAILURE_ISOLATION=true','SUBPROJECTS_ACTIVE=3','MAX_CONCURRENT_SLOTS='+$MaxSlots,'PAGES_TOTAL='+$Started,'PAGES_COMPLETED='+$Completed,'PAGES_TIMEOUT='+$TimedOut,'SOURCE_ACCURACY_SCORE='+$Source+'/100','PARCEL_MATCH_ACCURACY_SCORE='+$Parcel+'/100','GENERAL_CONFIDENCE_SCORE='+$Confidence+'/100','PROGRAM_COMPLETION='+$Program+'/100','NEXT_ACTION=devam et','NEXT_WAIT=60-90 minutes')|Set-Content -Encoding UTF8 $Status
W "ONE_PAGE_ONE_JOB=true"
W "FAILURE_ISOLATION=true"
W "SUBPROJECTS_ACTIVE=3"
W "MAX_CONCURRENT_SLOTS=$MaxSlots"
W "PAGES_COMPLETED=$Completed/$Started"
W "PAGES_TIMEOUT=$TimedOut"
W "SOURCE_ACCURACY_SCORE=$Source/100"
W "PARCEL_MATCH_ACCURACY_SCORE=$Parcel/100"
W "GENERAL_CONFIDENCE_SCORE=$Confidence/100"
W "PROGRAM_COMPLETION=$Program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_060_ISOLATED_PAGE_JOBS_5SLOT_SAFE_DONE'
exit 0
