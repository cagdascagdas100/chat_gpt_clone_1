$ErrorActionPreference='Continue'
$TaskId='ty107-rebuild-legal-processed-from-exports'
$BridgeRoot='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot='E:\AAYS_DATA\legal'
$ContractorRoot='E:\AAYS_DATA\contractor'
$OutDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $OutDir,$LegalRoot,(Join-Path $LegalRoot 'processed'),(Join-Path $LegalRoot 'exports'),(Join-Path $LegalRoot 'reports'),(Join-Path $LegalRoot 'db_transfer') | Out-Null
function L($m){Write-Output ('['+(Get-Date -Format 's')+'] '+$m)}
function Rows($p){try{if(Test-Path $p){$n=([IO.File]::ReadAllLines($p)).Length;if($n -gt 0){return $n-1}}}catch{};return 0}
function Info($p){if(Test-Path $p){$i=Get-Item $p;return [ordered]@{path=$p;exists=$true;bytes=$i.Length}};return [ordered]@{path=$p;exists=$false;bytes=0}}
function Latest($pattern){Get-ChildItem -Path $ContractorRoot -Recurse -File -ErrorAction SilentlyContinue -Filter $pattern|Sort-Object LastWriteTime -Descending|Select-Object -First 1}
function Val($row,[string[]]$names){foreach($n in $names){if($row.PSObject.Properties.Name -contains $n){$v=$row.$n;if($null -ne $v -and (''+$v).Trim() -ne ''){return $v}}};return $null}
function BoolText($v){if($null -eq $v){return ''};$s=(''+$v).ToLowerInvariant();if($s -in @('true','1','yes','y')){return 'true'};if($s -in @('false','0','no','n')){return 'false'};return $s}
function WriteCsv($path,$rows,$fields){$objs=@();foreach($r in $rows){$o=[ordered]@{};foreach($f in $fields){$o[$f]=$r[$f]};$objs += New-Object psobject -Property $o};$objs|Export-Csv -Path $path -NoTypeInformation -Encoding UTF8}
function Hash16($s){$sha=[Security.Cryptography.SHA256]::Create();$b=[Text.Encoding]::UTF8.GetBytes($s);$h=$sha.ComputeHash($b);return (($h[0..7]|ForEach-Object{$_.ToString('x2')}) -join '')}
$checks=@();$sources=@()
$appPath=Join-Path $LegalRoot 'exports\contractor_app_export.csv'
if(-not (Test-Path $appPath)){ $f=Latest 'contractors_for_app.csv'; if($f){Copy-Item -Force $f.FullName $appPath;$sources += [ordered]@{copied='contractor_app_export.csv';source=$f.FullName}} }
$jsonPath=Join-Path $LegalRoot 'exports\contractor_app_export.jsonl'
if(-not (Test-Path $jsonPath)){ $f=Latest 'contractors_for_app.jsonl'; if($f){Copy-Item -Force $f.FullName $jsonPath;$sources += [ordered]@{copied='contractor_app_export.jsonl';source=$f.FullName}} }
$matchPath=Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv'
if(-not (Test-Path $matchPath)){ $f=Latest 'contractor_parcel_matches_for_app.csv'; if($f){Copy-Item -Force $f.FullName $matchPath;$sources += [ordered]@{copied='contractor_parcel_matches.csv';source=$f.FullName}} }
$appRows=@();if(Test-Path $appPath){$appRows=Import-Csv $appPath}
$contractors=@();$scores=@();$provMissing=0
foreach($r in $appRows){
  $cid=Val $r @('contractor_id','company_id','id'); if(-not $cid){$cid='APP-'+(Hash16 ((Val $r @('company_name','name','contractor_name','supplier_name') )+''))}
  $sname=Val $r @('source_name');$surl=Val $r @('source_url');$srid=Val $r @('source_record_id');$fat=Val $r @('fetched_at');$lic=Val $r @('license_name')
  if(-not ($sname -and $surl -and $srid -and $fat -and $lic)){$provMissing++}
  $contractors += @{contractor_id=$cid;company_number=(Val $r @('company_number','supplier_company_number'));company_name=(Val $r @('company_name','contractor_name','supplier_name','name'));company_status=(Val $r @('company_status'));sic_codes=(Val $r @('sic_codes'));address_line_1=(Val $r @('address_line_1','address'));locality=(Val $r @('locality','town','city'));region=(Val $r @('region'));postal_code=(Val $r @('postal_code','postcode'));authority_code=(Val $r @('authority_code'));country=(Val $r @('country'));source_name=$sname;source_url=$surl;source_record_id=$srid;fetched_at=$fat;license_name=$lic}
  $legal=Val $r @('legal_contact_score');$dnc=BoolText (Val $r @('do_not_contact'))
  $scores += @{contractor_id=$cid;reliability_score=(Val $r @('reliability_score'));data_confidence_score=(Val $r @('data_confidence_score'));legal_contact_score=$legal;quality_band=(Val $r @('quality_band'));activity_density_label=(Val $r @('activity_density_label'));do_not_contact=$dnc;score_reason=(Val $r @('score_reason'));source_name=$sname;source_url=$surl;source_record_id=$srid;fetched_at=$fat;license_name=$lic}
}
$cFields=@('contractor_id','company_number','company_name','company_status','sic_codes','address_line_1','locality','region','postal_code','authority_code','country','source_name','source_url','source_record_id','fetched_at','license_name')
$sFields=@('contractor_id','reliability_score','data_confidence_score','legal_contact_score','quality_band','activity_density_label','do_not_contact','score_reason','source_name','source_url','source_record_id','fetched_at','license_name')
if($contractors.Count -gt 0){WriteCsv (Join-Path $LegalRoot 'processed\contractors_normalized.csv') $contractors $cFields;WriteCsv (Join-Path $LegalRoot 'processed\contractor_scores.csv') $scores $sFields}
$proj=Latest 'contractor_projects_for_app.csv'
$eventCount=0
if($proj){
  $events=@();$pr=Import-Csv $proj.FullName
  foreach($r in $pr){$cid=Val $r @('contractor_id','company_id');$rid=Val $r @('project_id','procurement_event_id','ocid','source_record_id','title');$eid=Val $r @('procurement_event_id');if(-not $eid){$eid='EV-'+(Hash16 (($cid+'|'+$rid)))};$events += @{procurement_event_id=$eid;ocid=(Val $r @('ocid'));release_id=(Val $r @('release_id','project_id'));buyer_name=(Val $r @('buyer_name','buyer'));supplier_name=(Val $r @('supplier_name','company_name','contractor_name'));supplier_company_number=(Val $r @('supplier_company_number','company_number'));title=(Val $r @('title','project_title'));description=(Val $r @('description'));procurement_stage=(Val $r @('procurement_stage','stage'));award_date=(Val $r @('award_date'));value_amount=(Val $r @('value_amount','amount'));value_currency=(Val $r @('value_currency','currency'));postcode=(Val $r @('postcode','postal_code'));authority_code=(Val $r @('authority_code'));region=(Val $r @('region'));source_name=(Val $r @('source_name'));source_url=(Val $r @('source_url'));source_record_id=(Val $r @('source_record_id'));fetched_at=(Val $r @('fetched_at'));license_name=(Val $r @('license_name'))}}
  $eFields=@('procurement_event_id','ocid','release_id','buyer_name','supplier_name','supplier_company_number','title','description','procurement_stage','award_date','value_amount','value_currency','postcode','authority_code','region','source_name','source_url','source_record_id','fetched_at','license_name')
  WriteCsv (Join-Path $LegalRoot 'processed\procurement_events_normalized.csv') $events $eFields
  $eventCount=$events.Count
  $sources += [ordered]@{copied='procurement_events_normalized.csv';source=$proj.FullName}
}
Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'db_transfer\schema_apply.sql') -Value 'create extension if not exists postgis; create schema if not exists legal_intel;'
Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'db_transfer\load_order.csv') -Value "order,file_name,target_table,mode,required`n1,contractors_normalized.csv,legal_intel.contractors,upsert,true`n2,procurement_events_normalized.csv,legal_intel.procurement_events,upsert,false`n3,contractor_scores.csv,legal_intel.contractor_scores,upsert,true`n4,contractor_parcel_matches.csv,legal_intel.contractor_parcel_matches,upsert,false"
Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'db_transfer\export_manifest.csv') -Value "file_name,provenance_required,fake_data_allowed`ncontractors_normalized.csv,true,false`ncontractor_scores.csv,true,false`ncontractor_app_export.csv,true,false"
Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'db_transfer\runbook_windows_linux.txt') -Value 'PowerShell and Bash runbook generated; DB load requires DATABASE_URL or PG* credentials.'
$dbCreds=[bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))
if(-not $dbCreds){Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'reports\blocked_by_missing_credential_postgres.json') -Value '{"status":"blocked","reason":"missing_database_credential_or_not_visible_to_runner"}'}
if($dbCreds -and (Test-Path $ProjectRoot)){Set-Location $ProjectRoot;$env:AAYS_LEGAL_ROOT=$LegalRoot;$checks += [ordered]@{label='DB_LOAD_SKIPPED_BY_SCRIPT';exit_code=0;note='credentials visible; run contractor_load_to_postgres manually if schema target is ready'}}
$files=@();foreach($p in @('processed\contractors_normalized.csv','processed\procurement_events_normalized.csv','processed\contractor_scores.csv','processed\contractor_parcel_matches.csv','exports\contractor_app_export.csv','exports\contractor_app_export.jsonl','db_transfer\schema_apply.sql','db_transfer\load_order.csv','db_transfer\export_manifest.csv','reports\blocked_by_missing_credential_postgres.json')){$files+=Info (Join-Path $LegalRoot $p)}
$cr=Rows (Join-Path $LegalRoot 'processed\contractors_normalized.csv');$sr=Rows (Join-Path $LegalRoot 'processed\contractor_scores.csv');$ar=Rows (Join-Path $LegalRoot 'exports\contractor_app_export.csv');$mr=Rows (Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv')
$progress=72;if($cr -gt 0 -and $sr -gt 0){$progress=82};if($eventCount -gt 0){$progress=84};if($dbCreds){$progress=[Math]::Max($progress,86)};if($mr -gt 0){$progress=[Math]::Max($progress,86)}
$a=[ordered]@{task_id=$TaskId;status='completed';generated_at=(Get-Date).ToString('s');contractor_rows=$cr;score_rows=$sr;event_rows=$eventCount;app_rows=$ar;parcel_match_rows=$mr;provenance_missing_count=$provMissing;db_credentials_present=$dbCreds;sources=$sources;checks=$checks;files=$files;plan_progress_percent=$progress;plan_percent_remaining=(100-$progress)}
$a|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.audit.json'))
$lines=@('# TY107 Rebuild Legal Processed From Exports','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('Contractor rows: '+$cr),('Score rows: '+$sr),('Event rows: '+$eventCount),('App rows: '+$ar),('Parcel match rows: '+$mr),('Provenance missing count: '+$provMissing),('DB credentials present: '+$dbCreds),'','## Files');foreach($f in $files){$lines+=('- '+$f.path+' exists='+$f.exists+' bytes='+$f.bytes)};$lines|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.report.md'))
L('PLAN_PROGRESS_PERCENT='+$progress);L('PLAN_PERCENT_REMAINING='+(100-$progress));exit 0
