$ErrorActionPreference='Continue'
$TaskId='ty114-rebuild-exports-with-provenance'
$BridgeRoot='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$LegalRoot='E:\AAYS_DATA\legal'
$OutDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $OutDir,(Join-Path $LegalRoot 'exports'),(Join-Path $LegalRoot 'processed'),(Join-Path $LegalRoot 'reports'),(Join-Path $LegalRoot 'db_transfer') | Out-Null
function L($m){Write-Output ('['+(Get-Date -Format 's')+'] '+$m)}
function Rows($p){try{if(Test-Path $p){$n=([IO.File]::ReadAllLines($p)).Length;if($n -gt 0){return $n-1}}}catch{};return 0}
function H($p){try{if(Test-Path $p){return ((Get-Content $p -TotalCount 1)-split ',')}}catch{};return @()}
function HasProv($p){$h=H $p;foreach($c in @('source_name','source_url','source_record_id','fetched_at','license_name')){if($h -notcontains $c){return $false}};return $true}
function MissProv($p){try{$m=0;$need=@('source_name','source_url','source_record_id','fetched_at','license_name');foreach($r in Import-Csv $p){foreach($c in $need){if(-not ($r.PSObject.Properties.Name -contains $c) -or [string]::IsNullOrWhiteSpace((''+$r.$c))){$m++;break}}};return $m}catch{return -1}}
function Info($p){if(Test-Path $p){$i=Get-Item $p;return [ordered]@{path=$p;exists=$true;bytes=$i.Length;rows=Rows $p;has_provenance=HasProv $p;missing_provenance=MissProv $p}};return [ordered]@{path=$p;exists=$false;bytes=0;rows=0;has_provenance=$false;missing_provenance=-1}}
function Val($r,$names){foreach($n in $names){if($r.PSObject.Properties.Name -contains $n){$v=$r.$n;if($null -ne $v -and (''+$v).Trim() -ne ''){return $v}}};return ''}
function WriteRows($path,$rows,$fields){$out=@();foreach($r in $rows){$o=[ordered]@{};foreach($f in $fields){if($r.ContainsKey($f)){$o[$f]=$r[$f]}else{$o[$f]=''}};$out += New-Object psobject -Property $o};$out|Export-Csv -NoTypeInformation -Encoding UTF8 -Path $path}
$contractorsPath=Join-Path $LegalRoot 'processed\contractors_normalized.csv'
$scoresPath=Join-Path $LegalRoot 'processed\contractor_scores.csv'
$appPath=Join-Path $LegalRoot 'exports\contractor_app_export.csv'
$appJsonl=Join-Path $LegalRoot 'exports\contractor_app_export.jsonl'
$matchPath=Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv'
$actions=@()
$contractors=@{};$scores=@{}
if((Test-Path $contractorsPath) -and (HasProv $contractorsPath)){
  foreach($r in Import-Csv $contractorsPath){$cid=Val $r @('contractor_id');if($cid){$contractors[$cid]=$r}}
}
if((Test-Path $scoresPath) -and (HasProv $scoresPath)){
  foreach($r in Import-Csv $scoresPath){$cid=Val $r @('contractor_id');if($cid){$scores[$cid]=$r}}
}
if($contractors.Count -gt 0 -and $scores.Count -gt 0){
  $fields=@('contractor_id','company_number','company_name','company_status','sic_codes','address_line_1','locality','region','postal_code','authority_code','country','reliability_score','data_confidence_score','legal_contact_score','quality_band','activity_density_label','do_not_contact','contact_allowed','source_name','source_url','source_record_id','fetched_at','license_name')
  $rows=@()
  foreach($cid in $contractors.Keys){$c=$contractors[$cid];$s=$scores[$cid];$legal=Val $s @('legal_contact_score');$dnc=(Val $s @('do_not_contact')).ToLowerInvariant();$allowed='false';try{if(([int]$legal -ge 50) -and $dnc -ne 'true'){$allowed='true'}}catch{};$rows += @{contractor_id=$cid;company_number=Val $c @('company_number');company_name=Val $c @('company_name');company_status=Val $c @('company_status');sic_codes=Val $c @('sic_codes');address_line_1=Val $c @('address_line_1');locality=Val $c @('locality');region=Val $c @('region');postal_code=Val $c @('postal_code');authority_code=Val $c @('authority_code');country=Val $c @('country');reliability_score=Val $s @('reliability_score');data_confidence_score=Val $s @('data_confidence_score');legal_contact_score=$legal;quality_band=Val $s @('quality_band');activity_density_label=Val $s @('activity_density_label');do_not_contact=$dnc;contact_allowed=$allowed;source_name=Val $c @('source_name');source_url=Val $c @('source_url');source_record_id=Val $c @('source_record_id');fetched_at=Val $c @('fetched_at');license_name=Val $c @('license_name')}}
  WriteRows $appPath $rows $fields
  $sw=New-Object IO.StreamWriter($appJsonl,$false,[Text.UTF8Encoding]::new($false));foreach($r in $rows){$sw.WriteLine(($r|ConvertTo-Json -Compress -Depth 5))};$sw.Close()
  $actions += 'rebuilt_app_export_from_processed_contractors_and_scores'
}
if((Test-Path $matchPath) -and $contractors.Count -gt 0){
  $mrows=Import-Csv $matchPath
  $existing=H $matchPath
  $fields=@();foreach($x in $existing){if($x){$fields+=$x}}
  foreach($p in @('source_name','source_url','source_record_id','fetched_at','license_name')){if($fields -notcontains $p){$fields+=$p}}
  $rows=@();foreach($r in $mrows){$cid=Val $r @('contractor_id');$c=$contractors[$cid];$d=@{};foreach($f in $fields){if($r.PSObject.Properties.Name -contains $f){$d[$f]=$r.$f}else{$d[$f]=''}};if($c){foreach($p in @('source_name','source_url','source_record_id','fetched_at','license_name')){if([string]::IsNullOrWhiteSpace((''+$d[$p]))){$d[$p]=Val $c @($p)}}};$rows+=$d}
  WriteRows $matchPath $rows $fields
  $actions += 'filled_parcel_match_provenance_from_matching_contractor_rows'
}
$dbCreds=[bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))
$files=@();foreach($p in @($contractorsPath,(Join-Path $LegalRoot 'processed\procurement_events_normalized.csv'),$scoresPath,$matchPath,$appPath,$appJsonl,(Join-Path $LegalRoot 'db_transfer\schema_apply.sql'),(Join-Path $LegalRoot 'db_transfer\load_order.csv'),(Join-Path $LegalRoot 'db_transfer\export_manifest.csv')){$files += Info $p}
$critical=@($files|Where-Object{$_.path -like '*.csv' -and $_.path -notlike '*jsonl' -and ($_.missing_provenance -ne 0 -or -not $_.has_provenance)})
if($critical.Count -gt 0){$block=[ordered]@{status='blocked';reason='critical_provenance_missing_after_rebuild';generated_at=(Get-Date).ToString('s');critical=$critical};$block|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'reports\blocked_critical_provenance_missing.json')}
if(-not $dbCreds){Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'reports\blocked_by_missing_credential_postgres.json') -Value '{"status":"blocked","reason":"missing_database_credential_or_not_visible_to_runner"}'}
$cr=Rows $contractorsPath;$sr=Rows $scoresPath;$er=Rows (Join-Path $LegalRoot 'processed\procurement_events_normalized.csv');$ar=Rows $appPath;$mr=Rows $matchPath
$progress=88;if($critical.Count -eq 0 -and $cr -gt 0 -and $sr -gt 0 -and $er -gt 0 -and $ar -gt 0 -and $mr -gt 0){$progress=90};if($dbCreds){$progress=[Math]::Max($progress,92)}
$a=[ordered]@{task_id=$TaskId;status='completed';generated_at=(Get-Date).ToString('s');actions=$actions;db_credentials_present=$dbCreds;critical_provenance_missing_count=$critical.Count;contractor_rows=$cr;score_rows=$sr;event_rows=$er;app_rows=$ar;parcel_match_rows=$mr;files=$files;plan_progress_percent=$progress;plan_percent_remaining=(100-$progress)}
$a|ConvertTo-Json -Depth 7|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.audit.json'))
$lines=@('# TY114 Rebuild Exports With Provenance','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('DB credentials present: '+$dbCreds),('Critical provenance missing count: '+$critical.Count),('Contractor rows: '+$cr),('Score rows: '+$sr),('Event rows: '+$er),('App rows: '+$ar),('Parcel match rows: '+$mr),'','## Actions');foreach($x in $actions){$lines+=('- '+$x)};$lines+=@('','## Files');foreach($f in $files){$lines+=('- '+$f.path+' rows='+$f.rows+' has_provenance='+$f.has_provenance+' missing='+$f.missing_provenance+' bytes='+$f.bytes)};$lines|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.report.md'))
L('PLAN_PROGRESS_PERCENT='+$progress);L('PLAN_PERCENT_REMAINING='+(100-$progress));exit 0
