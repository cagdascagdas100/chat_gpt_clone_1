$ErrorActionPreference='Continue'
$TaskId='terrayield-estate-001-parcel-groups-and-agent-schema-20260519'
$BridgeRoot=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{'C:\AAYS_GITHUB_BRIDGE_CLEAN2'}
$OutRoot='E:\AAYS_DATA\estate_agents'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $OutRoot,$ResultDir | Out-Null
function Log($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function CsvEscape($v){ if($null -eq $v){return ''}; $s=[string]$v; if($s -match '[,"\r\n]'){return '"'+($s -replace '"','""')+'"'}; return $s }
Log "TASK=$TaskId"
Log 'MODE=estate_agent_parcel_group_seed_schema'
Log 'NO_DB_WRITE=true'
Log 'NO_SECRET_PRINT=true'
$minLon=-6.45; $maxLon=1.80; $minLat=49.85; $maxLat=55.85
$cols=10; $rows=20
$dx=($maxLon-$minLon)/$cols; $dy=($maxLat-$minLat)/$rows
$regionNames=@('South West','South Coast','South East','London / Home Counties','East of England','West Midlands','East Midlands','North West','Yorkshire / Humber','North East')
$groups=@()
$id=1
for($r=0;$r -lt $rows;$r++){
  for($c=0;$c -lt $cols;$c++){
    $lon1=[math]::Round($minLon+($c*$dx),6); $lon2=[math]::Round($minLon+(($c+1)*$dx),6)
    $lat1=[math]::Round($minLat+($r*$dy),6); $lat2=[math]::Round($minLat+(($r+1)*$dy),6)
    $centLon=[math]::Round(($lon1+$lon2)/2,6); $centLat=[math]::Round(($lat1+$lat2)/2,6)
    $band=[math]::Min([math]::Floor(($r/$rows)*$regionNames.Count),$regionNames.Count-1)
    $gid=('ENG-PG-{0:D3}' -f $id)
    $groups += [ordered]@{
      parcel_group_id=$gid
      group_index=$id
      grid_row=($r+1)
      grid_col=($c+1)
      region_band=$regionNames[$band]
      bbox_min_lon=$lon1
      bbox_min_lat=$lat1
      bbox_max_lon=$lon2
      bbox_max_lat=$lat2
      centroid_lon=$centLon
      centroid_lat=$centLat
      matching_rule='parcel centroid within bbox; later refine by admin boundary/postcode/local authority'
      intended_use='agent coverage lookup and later TerraYield parcel_id join'
    }
    $id++
  }
}
$groupCsv=Join-Path $OutRoot 'england_parcel_groups_200_seed.csv'
$headers=@('parcel_group_id','group_index','grid_row','grid_col','region_band','bbox_min_lon','bbox_min_lat','bbox_max_lon','bbox_max_lat','centroid_lon','centroid_lat','matching_rule','intended_use')
$lines=@(($headers -join ','))
foreach($g in $groups){$lines += (($headers|ForEach-Object{CsvEscape $g[$_]}) -join ',')}
$lines|Set-Content -Encoding UTF8 -Path $groupCsv
$agentCsv=Join-Path $OutRoot 'estate_agent_directory_seed_schema.csv'
$agentHeaders=@('agent_id','agent_or_branch_name','company_name','person_name','brand_or_network','phone','email','office_address','website_url','source_url','source_type','evidence_summary','previous_work_summary','postcode','local_authority','county_or_region','latitude','longitude','coverage_parcel_group_ids','coverage_rule','trust_score_10','truth_score_name_4','truth_score_phone_4','truth_score_address_4','truth_score_website_4','truth_score_coverage_4','overall_data_truth_score_4','notes','program_parcel_ids_to_link_later')
($agentHeaders -join ',')|Set-Content -Encoding UTF8 -Path $agentCsv
$planPath=Join-Path $OutRoot 'estate_agent_parcel_group_pipeline_plan.md'
$plan=@()
$plan+='# TerraYield Estate Agent Parcel Group Pipeline Plan'
$plan+=''
$plan+="Generated: $(Get-Date -Format s)"
$plan+="Task: $TaskId"
$plan+=''
$plan+='## Goal'
$plan+='Create an England estate-agent directory where each row is an agent/branch/company and coverage_parcel_group_ids lists the 200 seed parcel groups where that agent appears relevant. Later TerraYield parcel_id values will join to these parcel groups.'
$plan+=''
$plan+='## Phase 1 Completed by this task'
$plan+='- Create 200 seed England parcel groups using a regular bbox grid.'
$plan+='- Create the estate agent directory schema.'
$plan+='- Keep actual program parcel_id matching for the next Codex/local data join.'
$plan+=''
$plan+='## Next automated phases'
$plan+='1. Collect candidate estate agents from open/allowed sources and local existing artifacts.'
$plan+='2. Normalize names, addresses, phones, web URLs, postcode/local authority, and coordinates.'
$plan+='3. Map each agent to one or more parcel_group_ids by coordinate, postcode/admin area, and evidence locality.'
$plan+='4. Score trust_score_10 using evidence count, source diversity, contact completeness, website consistency, and previous-work signals.'
$plan+='5. Score every factual field on 0-4 truth scale.'
$plan+='6. Export CSV/XLSX for user review and later TerraYield parcel_id join.'
$plan+=''
$plan+='## Important limitation'
$plan+='This task does not claim all England estate agents are collected yet. It creates the group framework and schema. Comprehensive agent collection must run in follow-up tasks and should avoid restricted scraping.'
$plan|Set-Content -Encoding UTF8 -Path $planPath
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# TerraYield Estate 001 Parcel Groups and Agent Schema','',"Generated: $(Get-Date -Format s)","Task: $TaskId",'','## Outputs',"- parcel_groups_csv: $groupCsv","- agent_schema_csv: $agentCsv","- plan: $planPath",'','## Counts',"- parcel_groups: $($groups.Count)","- agent_schema_columns: $($agentHeaders.Count)",'','## Progress','- parcel group framework: complete','- agent directory schema: complete','- actual agent collection: pending','- actual TerraYield parcel_id join: pending','','PLAN_PROGRESS_PERCENT=18','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE')
$r|Set-Content -Encoding UTF8 -Path $out
Log "PARCEL_GROUPS_CSV=$groupCsv"
Log "AGENT_SCHEMA_CSV=$agentCsv"
Log "PLAN_PATH=$planPath"
Log "REPORT_PATH=$out"
Log 'PLAN_PROGRESS_PERCENT=18'
Log 'TASK_COMPLETION=100/100'
exit 0
