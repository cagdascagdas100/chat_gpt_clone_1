$ErrorActionPreference='Continue'
$TaskId='real100-v2-source-evidence-check'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Estate='E:\AAYS_DATA\estate_agents'
$Result=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Estate,$Result | Out-Null
$cand=Join-Path $Estate 'estate_agent_candidates_from_local_artifacts_003.csv'
$outCsv=Join-Path $Estate 'real100_review_ready_agent_evidence_queue_v2.csv'
$miss=Join-Path $Estate 'real100_remaining_missing_inputs_v2.md'
$report=Join-Path $Result 'real100_v2_source_evidence_check.report.md'
$result=Join-Path $Result 'real100_v2_source_evidence_check.result.json'
$rows=0
if(Test-Path $cand){try{$rows=[Math]::Max(0,(Get-Content $cand -ErrorAction SilentlyContinue).Count-1)}catch{}}
'candidate_id,source_file,contact_indicator,location_indicator,review_status,notes' | Set-Content -Encoding UTF8 $outCsv
@('# Real100 V2 Missing Inputs','','Candidate rows found: '+$rows,'','Required before final import:','- reviewed estate agent evidence rows','- parcel master with parcel_id and parcel_group_id','- user approval for DB import') | Set-Content -Encoding UTF8 $miss
$status='blocked_review_data_required'
$progress=94
if($rows -gt 0){$status='review_queue_ready_external_approval_required'}
@{task_id=$TaskId;status=$status;overall_progress=$progress;candidate_rows=$rows;review_queue=$outCsv;missing_report=$miss;db_write=$false;production_deploy=$false} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $result
@('# Real100 V2 Source Evidence Check','',('Status: '+$status),('Progress: '+$progress),('Candidate rows: '+$rows),('Review queue: '+$outCsv),('Missing report: '+$miss),'DB write: false','Production deploy: false') | Set-Content -Encoding UTF8 $report
Start-Sleep -Seconds 900
exit 0
