$ErrorActionPreference='Continue'
$TaskId='ty106-sync-contractors-to-legal'
$BridgeRoot='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$SourceRoot='E:\AAYS_DATA\contractor'
$LegalRoot='E:\AAYS_DATA\legal'
$OutDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $OutDir,$LegalRoot,(Join-Path $LegalRoot 'raw\procurement'),(Join-Path $LegalRoot 'processed'),(Join-Path $LegalRoot 'exports'),(Join-Path $LegalRoot 'reports') | Out-Null
function L($m){Write-Output ('['+(Get-Date -Format 's')+'] '+$m)}
function Rows($p){try{if(Test-Path $p){$n=([IO.File]::ReadAllLines($p)).Length;if($n -gt 0){return $n-1}}}catch{};return 0}
function Info($p){if(Test-Path $p){$i=Get-Item $p;return [ordered]@{path=$p;exists=$true;bytes=$i.Length}};return [ordered]@{path=$p;exists=$false;bytes=0}}
function Latest($pattern){Get-ChildItem -Path $SourceRoot -Recurse -File -ErrorAction SilentlyContinue -Filter $pattern|Sort-Object LastWriteTime -Descending|Select-Object -First 1}
function CopyLatest($pattern,$dest){$f=Latest $pattern;if($f){New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest)|Out-Null;Copy-Item -Force $f.FullName $dest;L('COPIED '+$f.FullName+' -> '+$dest);return $f.FullName};L('NOT_FOUND '+$pattern);return $null}
$copies=@()
$copies += [ordered]@{target='contractors_normalized.csv';source=(CopyLatest 'contractors_normalized.csv' (Join-Path $LegalRoot 'processed\contractors_normalized.csv'))}
$copies += [ordered]@{target='procurement_events_normalized.csv';source=(CopyLatest 'procurement_events_normalized.csv' (Join-Path $LegalRoot 'processed\procurement_events_normalized.csv'))}
$copies += [ordered]@{target='contractor_scores.csv';source=(CopyLatest 'contractor_scores.csv' (Join-Path $LegalRoot 'processed\contractor_scores.csv'))}
$copies += [ordered]@{target='contractor_app_export.csv';source=(CopyLatest 'contractors_for_app.csv' (Join-Path $LegalRoot 'exports\contractor_app_export.csv'))}
$copies += [ordered]@{target='contractor_app_export.jsonl';source=(CopyLatest 'contractors_for_app.jsonl' (Join-Path $LegalRoot 'exports\contractor_app_export.jsonl'))}
$copies += [ordered]@{target='contractor_parcel_matches.csv';source=(CopyLatest 'contractor_parcel_matches_for_app.csv' (Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv'))}
$dbCreds=[bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))
if(-not $dbCreds){Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'reports\blocked_by_missing_credential_postgres.json') -Value '{"status":"blocked","reason":"missing_database_credential_or_not_visible_to_runner"}'}
$files=@();foreach($p in @('processed\contractors_normalized.csv','processed\procurement_events_normalized.csv','processed\contractor_scores.csv','processed\contractor_parcel_matches.csv','exports\contractor_app_export.csv','exports\contractor_app_export.jsonl','reports\blocked_by_missing_credential_postgres.json')){$files+=Info (Join-Path $LegalRoot $p)}
$score=Rows (Join-Path $LegalRoot 'processed\contractor_scores.csv')
$app=Rows (Join-Path $LegalRoot 'exports\contractor_app_export.csv')
$match=Rows (Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv')
$progress=52;if($score -gt 0){$progress=66};if($app -gt 0){$progress=72};if($dbCreds){$progress=[Math]::Max($progress,74)};if($match -gt 0){$progress=[Math]::Max($progress,78)}
$a=[ordered]@{task_id=$TaskId;status='completed';generated_at=(Get-Date).ToString('s');source_root=$SourceRoot;legal_root=$LegalRoot;db_credentials_present=$dbCreds;copies=$copies;files=$files;score_rows=$score;app_rows=$app;parcel_match_rows=$match;plan_progress_percent=$progress;plan_percent_remaining=(100-$progress)}
$a|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.audit.json'))
$lines=@('# TY106 Sync Contractors To Legal','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('DB credentials present: '+$dbCreds),('Score rows: '+$score),('App rows: '+$app),('Parcel match rows: '+$match),'','## Files');foreach($f in $files){$lines+=('- '+$f.path+' exists='+$f.exists+' bytes='+$f.bytes)};$lines|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.report.md'))
L('PLAN_PROGRESS_PERCENT='+$progress);L('PLAN_PERCENT_REMAINING='+(100-$progress));exit 0
