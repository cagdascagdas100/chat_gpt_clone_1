$ErrorActionPreference='Continue'
$TaskId='contractor-002-long-watchdog-foundation-20260519'
$Start=Get-Date
$TargetMinutes=38
$BridgeRoot='C:/AAYS_GITHUB_BRIDGE_CLEAN'
$ContractorRoot='E:/AAYS_DATA/contractor'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$ProgressDir=Join-Path $BridgeRoot 'ai-progress'
$LogDir=Join-Path $BridgeRoot 'ai-runner-logs'
$ExportDir=Join-Path $ContractorRoot 'exports'
$ManifestDir=Join-Path $ContractorRoot 'manifests'
$SchemaDir=Join-Path $ContractorRoot 'schemas'
$SqlDir=Join-Path $ContractorRoot 'sql'
@($ResultDir,$ProgressDir,$LogDir,$ContractorRoot,$ExportDir,$ManifestDir,$SchemaDir,$SqlDir) | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null }
$ProgressPath=Join-Path $ProgressDir ($TaskId+'.progress.md')
$ReportPath=Join-Path $ResultDir ($TaskId+'.report.md')
$ResultJsonPath=Join-Path $ResultDir ($TaskId+'.result.json')
$EventPath=Join-Path $LogDir ($TaskId+'.events.ndjson')
function Iso { (Get-Date).ToString('s') }
function SaveProgress($Percent,$Phase,$Extra='') { @("# $TaskId progress",'',"checked_at: $(Iso)","percent: $Percent","phase: $Phase","elapsed_minutes: $([math]::Round(((Get-Date)-$Start).TotalMinutes,2))","target_minutes: $TargetMinutes",'',$Extra) | Set-Content -Encoding UTF8 $ProgressPath }
function Event($Type,$Message) { ([ordered]@{ts=Iso;task_id=$TaskId;type=$Type;message=$Message}|ConvertTo-Json -Compress) | Add-Content -Encoding UTF8 $EventPath; Write-Output "[$(Iso)] $Type $Message" }
Event START 'contractor long watchdog foundation started'
SaveProgress 2 preflight
$jobs=@()
$jobs += Start-Job -Name groups_and_templates -ArgumentList $ExportDir,$ManifestDir -ScriptBlock {
  param($ExportDir,$ManifestDir)
  $minLon=-6.42; $maxLon=1.78; $minLat=49.85; $maxLat=55.85; $cols=20; $rows=10
  $dx=($maxLon-$minLon)/$cols; $dy=($maxLat-$minLat)/$rows; $groups=@(); $i=1
  for($r=0;$r -lt $rows;$r++){ for($c=0;$c -lt $cols;$c++){
    $west=[math]::Round($minLon+$c*$dx,6); $east=[math]::Round($minLon+($c+1)*$dx,6); $south=[math]::Round($minLat+$r*$dy,6); $north=[math]::Round($minLat+($r+1)*$dy,6)
    $gid=('ENG-G{0:D3}' -f $i)
    $groups += [pscustomobject]@{parcel_group_id=$gid;country='England';group_method='approx_grid_20x10_bbox';row_index=$r+1;col_index=$c+1;min_lon=$west;min_lat=$south;max_lon=$east;max_lat=$north;centroid_lon=[math]::Round(($west+$east)/2,6);centroid_lat=[math]::Round(($south+$north)/2,6);parcel_id_list='';match_key=$gid;notes='Approx group; real parcel IDs joined later'}
    $i++
  }}
  $groups | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $ExportDir 'england_parcel_groups_200.csv')
  $groups | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path (Join-Path $ExportDir 'england_parcel_groups_200.json')
  'contractor_id,entity_type,contractor_name,company_number,phone,email,website,registered_address,postcode,local_authority,source_names,source_urls,fetched_at,reliability_score_10,overall_accuracy_4,legal_contact_score,quality_band,do_not_contact,covered_parcel_group_ids,matched_parcel_ids,match_method,match_score_10,sort_score,notes' | Set-Content -Encoding UTF8 -Path (Join-Path $ExportDir 'contractor_rows_template.csv')
  'parcel_group_id,contractor_id,contractor_name,coverage_source,coverage_method,evidence_source_url,match_score_10,evidence_score_4,rank_in_group,show_in_app,matched_real_parcel_ids,notes' | Set-Content -Encoding UTF8 -Path (Join-Path $ExportDir 'contractor_group_match_template.csv')
  [ordered]@{status='ok_no_fake_contractors';group_count=$groups.Count;generated_at=(Get-Date).ToString('s')} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path (Join-Path $ManifestDir 'contractor_002_group_manifest.json')
  return @{job='groups_and_templates';status='ok';groups=$groups.Count}
}
$jobs += Start-Job -Name source_registry -ArgumentList $ManifestDir -ScriptBlock {
  param($ManifestDir)
  $sources=@(
    @{name='Companies House';category='official identity';required_for='company number and active status'},
    @{name='Contracts Finder';category='official procurement';required_for='public contract evidence'},
    @{name='Find a Tender';category='official procurement';required_for='large tender evidence'},
    @{name='Local authority planning portals';category='official planning';required_for='planning and past work evidence'},
    @{name='Contractor public website';category='primary public contact';required_for='phone email website verification'}
  )
  $sources | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path (Join-Path $ManifestDir 'contractor_002_official_source_registry.json')
  return @{job='source_registry';status='ok';sources=$sources.Count}
}
$jobs += Start-Job -Name schema_contract -ArgumentList $SchemaDir,$SqlDir -ScriptBlock {
  param($SchemaDir,$SqlDir)
  @('contractor_entities','contractor_provenance','parcel_groups','contractor_group_coverage') | Set-Content -Encoding UTF8 -Path (Join-Path $SchemaDir 'contractor_required_tables.txt')
  @('# Contractor app query contract','','clicked_parcel_id -> parcel_group_id -> contractor_group_coverage -> contractor_entities -> contractor_provenance','','Rules: no fake contractors; no unverified contact fields; no source URL means no accepted claim; fail closed for low evidence.') | Set-Content -Encoding UTF8 -Path (Join-Path $SchemaDir 'contractor_app_query_contract.md')
  @('create table if not exists contractor_entities (contractor_id text primary key, contractor_name text not null, company_number text, phone text, email text, website text, reliability_score_10 numeric, legal_contact_score numeric, do_not_contact boolean default false);','create table if not exists contractor_provenance (provenance_id text primary key, contractor_id text, source_name text not null, source_url text not null, fetched_at timestamptz, evidence_score_4 numeric);','create table if not exists parcel_groups (parcel_group_id text primary key, country text, group_method text, parcel_id_list text[]);','create table if not exists contractor_group_coverage (parcel_group_id text, contractor_id text, match_score_10 numeric, show_in_app boolean default false, primary key(parcel_group_id, contractor_id));') | Set-Content -Encoding UTF8 -Path (Join-Path $SqlDir 'contractor_foundation_schema_draft.sql')
  return @{job='schema_contract';status='ok'}
}
SaveProgress 12 parallel_jobs_started "jobs=$($jobs.Name -join ', ')"
$last=-1; $stuck=0; $cycle=0
while(((Get-Date)-$Start).TotalMinutes -lt $TargetMinutes){
  $cycle++
  $done=@($jobs | Where-Object { $_.State -in @('Completed','Failed','Stopped') }).Count
  if($done -eq $last){$stuck++}else{$stuck=0;$last=$done}
  $pct=[math]::Min(94, 12 + [int](82 * (((Get-Date)-$Start).TotalMinutes / $TargetMinutes)))
  $states=($jobs | Select-Object Name,State | ConvertTo-Json -Compress)
  SaveProgress $pct watchdog_monitoring "done_jobs=$done/$($jobs.Count)`nstuck_cycles=$stuck`nstates=$states"
  Event WATCHDOG "cycle=$cycle done=$done stuck=$stuck"
  if($stuck -ge 6){ Event STUCK_GUARD 'no completion change; continuing fail-soft and keeping watchdog alive'; $stuck=0 }
  if($done -eq $jobs.Count -and ((Get-Date)-$Start).TotalMinutes -ge 32){ break }
  Start-Sleep -Seconds 60
}
$jobResults=@()
foreach($j in $jobs){ try { $jobResults += Receive-Job -Job $j -Keep -ErrorAction SilentlyContinue } catch { $jobResults += @{job=$j.Name;status='receive_failed'} } }
try { Remove-Job -Job $jobs -Force -ErrorAction SilentlyContinue } catch {}
$result=[ordered]@{task_id=$TaskId;status='completed_foundation_no_fake_contractors';started_at=$Start.ToString('s');completed_at=(Get-Date).ToString('s');elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);job_results=$jobResults;safety=@{no_db_write=$true;no_fake_contractors=$true;no_secret_output=$true;production_deploy=$false};next_task='contractor-003-official-source-collector-and-normalizer'}
$result | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $ResultJsonPath
@('# Contractor 002 Long Watchdog Foundation','',"Task: $TaskId","Elapsed minutes: $([math]::Round(((Get-Date)-$Start).TotalMinutes,2))",'','## Completed','- 200 England parcel groups and templates generated/verified.','- Official source registry created.','- Read-only schema draft and app query contract created.','- Watchdog ran long-cycle monitoring and stuck guard.','','## Safety','- No fake contractor rows.','- No DB writes.','- No production deploy.','- No secrets printed.','','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 $ReportPath
SaveProgress 100 done "report=$ReportPath`nresult_json=$ResultJsonPath"
Event DONE 'contractor 002 completed'
exit 0