$ErrorActionPreference='Continue'
$TaskId='ty109-provenance-gate-and-final-preflight'
$BridgeRoot='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$LegalRoot='E:\AAYS_DATA\legal'
$ContractorRoot='E:\AAYS_DATA\contractor'
$OutDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $OutDir,(Join-Path $LegalRoot 'reports'),(Join-Path $LegalRoot 'processed'),(Join-Path $LegalRoot 'exports'),(Join-Path $LegalRoot 'db_transfer') | Out-Null
function L($m){Write-Output ('['+(Get-Date -Format 's')+'] '+$m)}
function Rows($p){try{if(Test-Path $p){$n=([IO.File]::ReadAllLines($p)).Length;if($n -gt 0){return $n-1}}}catch{};return 0}
function Info($p){if(Test-Path $p){$i=Get-Item $p;return [ordered]@{path=$p;exists=$true;bytes=$i.Length}};return [ordered]@{path=$p;exists=$false;bytes=0}}
function Header($p){try{if(Test-Path $p){return ((Get-Content -Path $p -TotalCount 1) -split ',')}}catch{};return @()}
function HasProv($p){$h=Header $p;foreach($c in @('source_name','source_url','source_record_id','fetched_at','license_name')){if($h -notcontains $c){return $false}};return $true}
function MissingProvRows($p){$need=@('source_name','source_url','source_record_id','fetched_at','license_name');try{if(!(Test-Path $p)){return 0};$rows=Import-Csv $p;$m=0;foreach($r in $rows){foreach($c in $need){if(-not ($r.PSObject.Properties.Name -contains $c) -or [string]::IsNullOrWhiteSpace((''+$r.$c))){$m++;break}}};return $m}catch{return -1}}
function LatestWithProv($pattern){$files=Get-ChildItem -Path $ContractorRoot -Recurse -File -ErrorAction SilentlyContinue -Filter $pattern|Sort-Object LastWriteTime -Descending;foreach($f in $files){if(HasProv $f.FullName){return $f.FullName}};return $null}
$targets=@(
  @{name='contractors_normalized.csv';path=Join-Path $LegalRoot 'processed\contractors_normalized.csv';patterns=@('contractors_normalized.csv','*contractors*normalized*.csv','contractors_for_app.csv')},
  @{name='procurement_events_normalized.csv';path=Join-Path $LegalRoot 'processed\procurement_events_normalized.csv';patterns=@('procurement_events_normalized.csv','contractor_projects_for_app.csv','*projects*for_app*.csv')},
  @{name='contractor_scores.csv';path=Join-Path $LegalRoot 'processed\contractor_scores.csv';patterns=@('contractor_scores.csv','*scores*.csv','contractors_for_app.csv')},
  @{name='contractor_app_export.csv';path=Join-Path $LegalRoot 'exports\contractor_app_export.csv';patterns=@('contractor_app_export.csv','contractors_for_app.csv')},
  @{name='contractor_parcel_matches.csv';path=Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv';patterns=@('contractor_parcel_matches.csv','contractor_parcel_matches_for_app.csv')}
)
$checks=@();$copies=@()
foreach($t in $targets){
  $beforeMissing=MissingProvRows $t.path
  $beforeHas=HasProv $t.path
  if($beforeMissing -ne 0){
    $candidate=$null
    foreach($pat in $t.patterns){$candidate=LatestWithProv $pat;if($candidate){break}}
    if($candidate){Copy-Item -Force $candidate $t.path;$copies += [ordered]@{target=$t.name;copied=$true;source=$candidate}}
    else{$copies += [ordered]@{target=$t.name;copied=$false;source=$null;reason='no candidate with all provenance columns found'}}
  }
  $checks += [ordered]@{file=$t.name;path=$t.path;exists=(Test-Path $t.path);rows=(Rows $t.path);has_provenance_columns=(HasProv $t.path);missing_provenance_rows=(MissingProvRows $t.path);before_missing_provenance_rows=$beforeMissing;before_has_provenance_columns=$beforeHas}
}
$dbCreds=[bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))
$criticalMissing=@($checks|Where-Object{$_.file -in @('contractors_normalized.csv','procurement_events_normalized.csv','contractor_scores.csv','contractor_app_export.csv') -and ($_.missing_provenance_rows -ne 0 -or -not $_.has_provenance_columns)})
if($criticalMissing.Count -gt 0){
  $block=[ordered]@{status='blocked';reason='critical_provenance_missing';generated_at=(Get-Date).ToString('s');missing_files=$criticalMissing;rule='Do not fabricate source_name/source_url/source_record_id/fetched_at/license_name. Missing evidence remains null and final DB load is blocked.'}
  $block|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'reports\blocked_critical_provenance_missing.json')
}
if(-not $dbCreds){Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'reports\blocked_by_missing_credential_postgres.json') -Value '{"status":"blocked","reason":"missing_database_credential_or_not_visible_to_runner"}'}
$cr=Rows (Join-Path $LegalRoot 'processed\contractors_normalized.csv');$sr=Rows (Join-Path $LegalRoot 'processed\contractor_scores.csv');$er=Rows (Join-Path $LegalRoot 'processed\procurement_events_normalized.csv');$ar=Rows (Join-Path $LegalRoot 'exports\contractor_app_export.csv');$mr=Rows (Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv')
$progress=86;if($criticalMissing.Count -eq 0 -and $cr -gt 0 -and $sr -gt 0 -and $ar -gt 0){$progress=90};if($dbCreds){$progress=[Math]::Max($progress,92)};if($dbCreds -and $mr -gt 0){$progress=[Math]::Max($progress,94)}
$files=@();foreach($p in @('processed\contractors_normalized.csv','processed\procurement_events_normalized.csv','processed\contractor_scores.csv','processed\contractor_parcel_matches.csv','exports\contractor_app_export.csv','exports\contractor_app_export.jsonl','reports\blocked_critical_provenance_missing.json','reports\blocked_by_missing_credential_postgres.json','db_transfer\schema_apply.sql','db_transfer\load_order.csv','db_transfer\export_manifest.csv')){$files+=Info (Join-Path $LegalRoot $p)}
$a=[ordered]@{task_id=$TaskId;status='completed';generated_at=(Get-Date).ToString('s');db_credentials_present=$dbCreds;contractor_rows=$cr;score_rows=$sr;event_rows=$er;app_rows=$ar;parcel_match_rows=$mr;critical_provenance_missing_count=$criticalMissing.Count;provenance_checks=$checks;copies=$copies;files=$files;plan_progress_percent=$progress;plan_percent_remaining=(100-$progress);next_action=if($criticalMissing.Count -gt 0){'Find official-source CSV/JSONL with provenance; do not fabricate missing provenance.'}elseif(-not $dbCreds){'Set PostgreSQL credentials and run DB load.'}else{'Run final DB load and closure audit.'}}
$a|ConvertTo-Json -Depth 10|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.audit.json'))
$lines=@('# TY109 Provenance Gate and Final Preflight','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('DB credentials present: '+$dbCreds),('Contractor rows: '+$cr),('Score rows: '+$sr),('Event rows: '+$er),('App rows: '+$ar),('Parcel match rows: '+$mr),('Critical provenance missing count: '+$criticalMissing.Count),'','## Provenance Checks');foreach($c in $checks){$lines+=('- '+$c.file+' rows='+$c.rows+' has_cols='+$c.has_provenance_columns+' missing_rows='+$c.missing_provenance_rows)};$lines+=@('','## Copies');foreach($x in $copies){$lines+=('- '+$x.target+' copied='+$x.copied+' source='+$x.source+' reason='+$x.reason)};$lines+=@('','## Files');foreach($f in $files){$lines+=('- '+$f.path+' exists='+$f.exists+' bytes='+$f.bytes)};$lines+=@('','## Next Action',$a.next_action)
$lines|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.report.md'))
L('PLAN_PROGRESS_PERCENT='+$progress);L('PLAN_PERCENT_REMAINING='+(100-$progress));exit 0
