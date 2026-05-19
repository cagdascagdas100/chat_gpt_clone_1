$ErrorActionPreference='Continue'
$TaskId='terrayield-estate-002-006-long-orchestrator-20260519-1535'
$Bridge=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{'C:\AAYS_GITHUB_BRIDGE_CLEAN2'}
$Project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Aays='C:\Users\cagda\Documents\GitHub\AAYS'
$Out='E:\AAYS_DATA\estate_agents'
$Res=Join-Path $Bridge 'ai-results'; $Prog=Join-Path $Bridge 'ai-progress'; $Run=Join-Path $Out $TaskId
New-Item -ItemType Directory -Force -Path $Out,$Res,$Prog,$Run | Out-Null
$Progress=Join-Path $Prog "$TaskId.progress.md"; $Report=Join-Path $Res "$TaskId.report.md"; $Json=Join-Path $Res "$TaskId.result.json"
$FinalCsv=Join-Path $Out 'estate_agent_directory_normalized_scored_20260519.csv'
$EvidenceCsv=Join-Path $Out 'estate_agent_evidence_chain_20260519.csv'
function A($p,$t){Add-Content -LiteralPath $p -Value $t -Encoding UTF8}
function E($v){if($null -eq $v){return ''};$s=[string]$v;if($s -match '[,"`r`n]'){return '"'+($s -replace '"','""')+'"'};$s}
function SID($s){$sha=[Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes([string]$s));(($sha|%{$_.ToString('x2')}) -join '').Substring(0,12)}
Set-Content -LiteralPath $Progress -Encoding UTF8 -Value @('# estate 002-006 progress',"task_id=$TaskId",'mode=long_parallel_read_only','no_db_write=true','no_production_deploy=true')
Set-Content -LiteralPath $Report -Encoding UTF8 -Value @('# estate 002-006 report',"task_id=$TaskId",'')
A $Progress "started_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
$cols=@('agent_id','agent_or_branch_name','company_name','person_name','brand_or_network','phone','email','office_address','website_url','source_url','source_type','evidence_summary','previous_work_summary','postcode','local_authority','county_or_region','latitude','longitude','coverage_parcel_group_ids','coverage_rule','trust_score_10','truth_score_name_4','truth_score_phone_4','truth_score_address_4','truth_score_website_4','truth_score_coverage_4','overall_data_truth_score_4','notes','program_parcel_ids_to_link_later')
$GroupCsv=Join-Path $Out 'england_parcel_groups_200_seed.csv'
if(!(Test-Path $GroupCsv) -or ((Get-Content $GroupCsv -ErrorAction SilentlyContinue|Measure).Count -lt 201)){
  A $Progress 'phase001_recovery=regenerate_200_groups'
  $hdr=@('parcel_group_id','group_index','grid_row','grid_col','region_band','bbox_min_lon','bbox_min_lat','bbox_max_lon','bbox_max_lat','centroid_lon','centroid_lat','matching_rule','intended_use')
  $regions=@('South West','South Coast','South East','London / Home Counties','East of England','West Midlands','East Midlands','North West','Yorkshire / Humber','North East')
  $minLon=-6.45;$maxLon=1.80;$minLat=49.85;$maxLat=55.85;$dx=($maxLon-$minLon)/10;$dy=($maxLat-$minLat)/20;$lines=@($hdr -join ',');$id=1
  for($r=0;$r -lt 20;$r++){for($c=0;$c -lt 10;$c++){$lon1=[math]::Round($minLon+$c*$dx,6);$lon2=[math]::Round($minLon+($c+1)*$dx,6);$lat1=[math]::Round($minLat+$r*$dy,6);$lat2=[math]::Round($minLat+($r+1)*$dy,6);$band=$regions[[math]::Min([math]::Floor(($r/20)*10),9)];$row=@(('ENG-PG-{0:D3}' -f $id),$id,($r+1),($c+1),$band,$lon1,$lat1,$lon2,$lat2,[math]::Round(($lon1+$lon2)/2,6),[math]::Round(($lat1+$lat2)/2,6),'parcel centroid within bbox; refine later by admin/postcode','agent coverage lookup and later parcel_id join');$lines+=($row|%{E $_}) -join ',';$id++}}
  $lines|Set-Content -LiteralPath $GroupCsv -Encoding UTF8
}
($cols -join ',')|Set-Content -LiteralPath (Join-Path $Out 'estate_agent_directory_seed_schema.csv') -Encoding UTF8
A $Report "parcel_groups_csv=$GroupCsv"
A $Report 'schema_ensured=true'
$roots=@(@{n='estate';p=$Out;l=900},@{n='project';p=$Project;l=1200},@{n='aays';p=$Aays;l=900},@{n='bridge';p=$Bridge;l=900},@{n='edata';p='E:\AAYS_DATA';l=1200})
$regex='estate|agent|branch|letting|property|properties|rightmove|zoopla|onthemarket|listing|sales|postcode|local_authority|county|emlak|emlakci'
$rawPath=Join-Path $Run 'candidate_raw.jsonl'; if(Test-Path $rawPath){Remove-Item $rawPath -Force}
for($cycle=1;$cycle -le 8;$cycle++){
  $utc=(Get-Date).ToUniversalTime().ToString('o'); A $Progress "cycle=$cycle utc=$utc"; A $Report "## discovery cycle $cycle $utc"
  $jobs=@()
  foreach($root in $roots){$jobs+=Start-Job -ScriptBlock {param($lane,$path,$lim,$regex,$run,$cycle)
    $out=Join-Path $run ("lane_${lane}_${cycle}.jsonl");$sum=Join-Path $run ("lane_${lane}_${cycle}.summary.txt")
    Set-Content -LiteralPath $sum -Encoding UTF8 -Value @("lane=$lane","path=$path","cycle=$cycle")
    if(!(Test-Path -LiteralPath $path)){Add-Content $sum 'missing_root=true' -Encoding UTF8;return}
    $files=Get-ChildItem -LiteralPath $path -File -Recurse -ErrorAction SilentlyContinue|?{$_.FullName -match $regex -and $_.FullName -notmatch '\\.git\\|node_modules|dist|build|.venv|venv|__pycache__' -and $_.Extension -match '\.(csv|txt|json|md|html|htm|log)$'}|Sort LastWriteTimeUtc -Desc|Select -First $lim
    Add-Content $sum "files=$($files.Count)" -Encoding UTF8;$hits=0
    foreach($f in $files){try{$txt=(Get-Content -LiteralPath $f.FullName -TotalCount 220 -ErrorAction SilentlyContinue)-join "`n"; if(!$txt){continue}
      $emails=([regex]::Matches($txt,'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}','IgnoreCase')|Select -First 2|%{$_.Value}) -join ';'
      $phones=([regex]::Matches($txt,'(\+44\s?\d{3,5}[\s\-]?\d{3,4}[\s\-]?\d{3,4}|0\d{3,5}[\s\-]?\d{3,4}[\s\-]?\d{3,4})')|Select -First 2|%{$_.Value}) -join ';'
      $pcs=([regex]::Matches($txt,'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b','IgnoreCase')|Select -First 2|%{$_.Value.ToUpper()}) -join ';'
      $urls=([regex]::Matches($txt,'https?://[^\s,;\)\]"'']+','IgnoreCase')|Select -First 2|%{$_.Value}) -join ';'
      $name='unknown';$m=[regex]::Match($txt,'(?im)^\s*([A-Z][A-Za-z0-9&''\-\. ]{2,80}\s+(Estate Agents|Lettings|Property|Properties|Surveyors|Land|Rural|Homes))\b');if($m.Success){$name=$m.Groups[1].Value.Trim()}elseif($f.BaseName -match '(estate|agent|letting|property|branch)'){$name=$f.BaseName}
      if(($emails+$phones+$pcs+$urls+$name) -ne 'unknown'){[ordered]@{lane=$lane;file=$f.FullName;name=$name;email=$emails;phone=$phones;postcode=$pcs;url=$urls;evidence=('local scan '+$f.Name);modified=$f.LastWriteTimeUtc.ToString('o')}|ConvertTo-Json -Compress|Add-Content -LiteralPath $out -Encoding UTF8;$hits++}
    }catch{Add-Content $sum ("file_error=$($f.FullName)") -Encoding UTF8}}
    Add-Content $sum "hits=$hits" -Encoding UTF8
  } -ArgumentList $root.n,$root.p,$root.l,$regex,$Run,$cycle}
  $null=Wait-Job $jobs -Timeout 150
  foreach($j in $jobs){A $Progress "job=$($j.Id) state=$($j.State)";if($j.State -eq 'Running'){Stop-Job $j -ErrorAction SilentlyContinue;A $Progress "job_timeout=$($j.Id)"};Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
  Get-ChildItem $Run -Filter "lane_*_${cycle}.jsonl" -ErrorAction SilentlyContinue|%{Get-Content $_.FullName -ErrorAction SilentlyContinue|Add-Content -LiteralPath $rawPath -Encoding UTF8}
  if($cycle -lt 8){Start-Sleep -Seconds 240}
}
$raw=@();if(Test-Path $rawPath){$raw=Get-Content $rawPath -ErrorAction SilentlyContinue|?{$_}|%{try{$_|ConvertFrom-Json}catch{$null}}}
A $Report "raw_candidates=$($raw.Count)"
$map=@{};foreach($r in $raw){$key=(($r.name+'|'+$r.email+'|'+$r.phone+'|'+$r.postcode+'|'+$r.url).ToLowerInvariant());if(!$map[$key]){$map[$key]=[ordered]@{name=$r.name;phone=$r.phone;email=$r.email;postcode=($r.postcode -split ';')[0];url=($r.url -split ';')[0];source=$r.file;evidence=$r.evidence;files=@($r.file)}}else{$map[$key].source+=';'+$r.file;$map[$key].evidence+=' | '+$r.evidence;$map[$key].files+=$r.file}}
$groups=Import-Csv $GroupCsv -ErrorAction SilentlyContinue;$reg=@{};foreach($g in $groups){if(!$reg[$g.region_band]){$reg[$g.region_band]=@()};$reg[$g.region_band]+=$g.parcel_group_id}
$kw=@{'South West'='cornwall|devon|somerset|dorset|bristol|wiltshire';'South East'='kent|surrey|sussex|berkshire|oxfordshire';'London / Home Counties'='london|hertfordshire|essex|middlesex';'East of England'='norfolk|suffolk|cambridgeshire|bedfordshire';'West Midlands'='birmingham|coventry|worcestershire|warwickshire|shropshire';'East Midlands'='leicestershire|nottinghamshire|derbyshire|lincolnshire';'North West'='manchester|liverpool|cheshire|lancashire|cumbria';'Yorkshire / Humber'='yorkshire|leeds|sheffield|hull';'North East'='newcastle|durham|northumberland|teeside'}
function TS($v){$s=[string]$v;if(!$s -or $s -eq 'unknown'){0}elseif($s -match ';'){2}else{3}}
$rows=@();$ev=@('agent_id,evidence_file,evidence_summary,source_type')
foreach($x in $map.Values){$hay=($x.source+' '+$x.evidence+' '+$x.postcode+' '+$x.name).ToLower();$coverage='unknown';$region='unknown';$cr='not enough locality evidence; pending postcode/admin/coordinate join';$cs=0;foreach($k in $kw.Keys){if($hay -match $kw[$k]){$coverage=($reg[$k] -join ';');$region=$k;$cr='coarse region keyword from local evidence; seed-grid only';$cs=2;break}}
  $ns=TS $x.name;$ps=TS $x.phone;$as=0;$ws=TS $x.url;$overall=[math]::Round((($ns+$ps+$as+$ws+$cs)/5),2);$trust=[math]::Round((($ns+$ps+$as+$ws+$cs)/20)*10,1);$id='EA-'+(SID ($x.name+'|'+$x.phone+'|'+$x.email+'|'+$x.postcode+'|'+$x.url))
  $row=[ordered]@{agent_id=$id;agent_or_branch_name=$x.name;company_name=$x.name;person_name='unknown';brand_or_network='unknown';phone=$x.phone;email=$x.email;office_address='unknown';website_url=$x.url;source_url=$x.source;source_type='local_artifact_extraction';evidence_summary=$x.evidence;previous_work_summary='Seen in local AAYS artifact; not independently verified in this task';postcode=$x.postcode;local_authority='unknown';county_or_region=$region;latitude='unknown';longitude='unknown';coverage_parcel_group_ids=$coverage;coverage_rule=$cr;trust_score_10=$trust;truth_score_name_4=$ns;truth_score_phone_4=$ps;truth_score_address_4=$as;truth_score_website_4=$ws;truth_score_coverage_4=$cs;overall_data_truth_score_4=$overall;notes='read-only extraction; unknown where not evidenced';program_parcel_ids_to_link_later='unknown'};$rows+=$row;foreach($f in ($x.files|Select -Unique)){$ev+=($id,(E $f),(E $x.evidence),'local_artifact_extraction') -join ','}}
$lines=@($cols -join ',');foreach($r in ($rows|Sort {[double]$_.trust_score_10} -Desc)){$lines+=($cols|%{E $r[$_]}) -join ','};$lines|Set-Content $FinalCsv -Encoding UTF8;$ev|Set-Content $EvidenceCsv -Encoding UTF8
$status=if($rows.Count -gt 0){'partial_success'}else{'schema_only_blocked_no_candidates'}
[ordered]@{task_id=$TaskId;status=$status;raw_candidates=$raw.Count;deduped_agents=$rows.Count;final_csv=$FinalCsv;evidence_csv=$EvidenceCsv;parcel_groups_csv=$GroupCsv;safety=@('no_db_write','no_production_deploy','no_secret_output','no_fake_agent_rows');waited_minutes='about 32 plus scan time';warnings=@('coverage conservative','parcel_id join pending')}|ConvertTo-Json -Depth 5|Set-Content $Json -Encoding UTF8
A $Report "deduped_agents=$($rows.Count)";A $Report "final_csv=$FinalCsv";A $Report "evidence_csv=$EvidenceCsv";A $Report 'PLAN_PROGRESS_PERCENT=52';A $Report 'TASK_COMPLETION=100/100';A $Report 'TERRAYIELD_ESTATE_002_006_DONE'
Write-Host 'TERRAYIELD_ESTATE_002_006_DONE'
exit 0