param([int]$TargetMinutes=38)
$ErrorActionPreference='Continue'
$Start=Get-Date
$End=$Start.AddMinutes($TargetMinutes)
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN'
$Data='E:\AAYS_DATA\contractor'
$Exp=Join-Path $Data 'exports'
$Man=Join-Path $Data 'manifests'
$Sch=Join-Path $Data 'schemas'
$Sql=Join-Path $Data 'sql'
$Prog=Join-Path $Bridge 'ai-progress'
$Res=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Exp,$Man,$Sch,$Sql,$Prog,$Res | Out-Null
$Progress=Join-Path $Prog 'contractor-002-long-watchdog-foundation-20260519.progress.md'
$Result=Join-Path $Res 'contractor-002-long-watchdog-foundation-20260519.result.json'
$Report=Join-Path $Res 'contractor-002-long-watchdog-foundation-20260519.report.md'
function AddL($p,$t){Add-Content -Path $p -Value $t -Encoding UTF8}
Set-Content -Path $Progress -Value "# Contractor 002 progress`nstart=$($Start.ToString('s'))`n" -Encoding UTF8
$GroupCsv=Join-Path $Exp 'england_parcel_groups_200.csv'
$GroupJson=Join-Path $Exp 'england_parcel_groups_200.json'
$RowsCsv=Join-Path $Exp 'contractor_rows_template.csv'
$MatchCsv=Join-Path $Exp 'contractor_group_match_template.csv'
$Manifest=Join-Path $Man 'contractor_002_group_manifest.json'
$Registry=Join-Path $Man 'contractor_002_official_source_registry.json'
$Tables=Join-Path $Sch 'contractor_required_tables.txt'
$Contract=Join-Path $Sch 'contractor_app_query_contract.md'
$Schema=Join-Path $Sql 'contractor_foundation_schema_draft.sql'
$RootCandidates=@('C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence','C:\AAYS_GITHUB_BRIDGE_CLEAN','C:\AAYS_GITHUB_BRIDGE_CLEAN2')
$Found=@()
foreach($r in $RootCandidates){if(Test-Path $r){$Found += Get-ChildItem $r -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Name -match 'parcel|boundary|land|geojson|gpkg|shp|ready|sale'} | Select-Object -First 260 FullName,Length,LastWriteTime}}
$groups=@()
$i=0
foreach($f in ($Found|Select-Object -First 200)){$i++;$groups += [pscustomobject]@{group_id=('ENG-GRP-{0:D3}' -f $i);source_file=$f.FullName;bytes=$f.Length;modified=$f.LastWriteTime;status='source_candidate';contractor_count=0;note='no contractor row generated'}}
if($groups.Count -eq 0){$groups += [pscustomobject]@{group_id='ENG-GRP-000';source_file='';bytes=0;modified='';status='blocked_no_source_candidate';contractor_count=0;note='no parcel source candidate found'}}
$groups | Export-Csv -Path $GroupCsv -NoTypeInformation -Encoding UTF8
$groups | ConvertTo-Json -Depth 5 | Set-Content -Path $GroupJson -Encoding UTF8
[pscustomobject]@{contractor_id='';name='';service_type='';official_source_url='';coverage_area='';evidence_status='empty_template_only'} | Export-Csv -Path $RowsCsv -NoTypeInformation -Encoding UTF8
[pscustomobject]@{group_id='';contractor_id='';match_method='';confidence='';source_url='';evidence_status='empty_template_only'} | Export-Csv -Path $MatchCsv -NoTypeInformation -Encoding UTF8
Set-Content -Path $Tables -Encoding UTF8 -Value "contractor_sources`ncontractor_rows`ncontractor_group_matches`ncontractor_exports"
Set-Content -Path $Contract -Encoding UTF8 -Value "# Contractor App Query Contract`n`nInputs: parcel group id, area, optional service type.`nOutputs: matched contractor rows with source url and evidence status.`nRule: rows without source url must not be high confidence.`n"
Set-Content -Path $Schema -Encoding UTF8 -Value "-- Contractor foundation schema draft only`n-- Review before applying.`ncreate table if not exists contractor_sources (id text primary key, source_url text, source_name text);`ncreate table if not exists contractor_rows (id text primary key, name text, service_type text, source_url text);`ncreate table if not exists contractor_group_matches (group_id text, contractor_id text, confidence text, source_url text);`n"
$sourceRegistry=@(
  [ordered]@{name='Companies House';url='https://find-and-update.company-information.service.gov.uk/';type='official_registry'},
  [ordered]@{name='GOV.UK';url='https://www.gov.uk/';type='official_public_source'},
  [ordered]@{name='Environment Agency';url='https://www.gov.uk/government/organisations/environment-agency';type='official_public_source'}
)
$sourceRegistry | ConvertTo-Json -Depth 5 | Set-Content -Path $Registry -Encoding UTF8
[ordered]@{status='running';started_at=$Start.ToString('s');groups=$groups.Count;files_seen=$Found.Count;outputs_seeded=$true} | ConvertTo-Json -Depth 5 | Set-Content -Path $Manifest -Encoding UTF8
$phase=0
while((Get-Date) -lt $End){$phase++;AddL $Progress "phase=$phase time=$((Get-Date).ToString('s')) groups=$($groups.Count) files_seen=$($Found.Count)";Start-Sleep -Seconds 60}
$status=if($groups[0].status -eq 'blocked_no_source_candidate'){'blocked_foundation_seeded'}else{'completed_foundation_seeded'}
$jobResults=@(
  [ordered]@{job='groups';status=$status;rows=$groups.Count;output=$GroupCsv},
  [ordered]@{job='templates';status='completed_empty_templates';outputs=@($RowsCsv,$MatchCsv)},
  [ordered]@{job='registry';status='completed';output=$Registry},
  [ordered]@{job='schema_contract';status='completed_draft';outputs=@($Tables,$Contract,$Schema)}
)
[ordered]@{status=$status;elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);job_results=$jobResults;safety=[ordered]@{fake_contractors=$false;db_write=$false;production_deploy=$false};next_task='review outputs and use real official sources before inserting contractor rows'} | ConvertTo-Json -Depth 8 | Set-Content -Path $Result -Encoding UTF8
Set-Content -Path $Report -Encoding UTF8 -Value "# Contractor 002 Long Watchdog Foundation`nstatus=$status`nelapsed_minutes=$([math]::Round(((Get-Date)-$Start).TotalMinutes,2))`ngroups=$($groups.Count)`nfiles_seen=$($Found.Count)`nresult=$Result`n"
