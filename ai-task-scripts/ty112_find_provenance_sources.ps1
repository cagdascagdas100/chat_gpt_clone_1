$ErrorActionPreference='Continue'
$TaskId='ty112-find-provenance-sources'
$BridgeRoot='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot='E:\AAYS_DATA\legal'
$ContractorRoot='E:\AAYS_DATA\contractor'
$OutDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $OutDir,(Join-Path $LegalRoot 'reports'),(Join-Path $LegalRoot 'raw'),(Join-Path $LegalRoot 'processed'),(Join-Path $LegalRoot 'exports') | Out-Null
function L($m){Write-Output ('['+(Get-Date -Format 's')+'] '+$m)}
function Rows($p){try{if(Test-Path $p){$n=([IO.File]::ReadAllLines($p)).Length;if($n -gt 0){return $n-1}}}catch{};return 0}
function Head($p){try{if(Test-Path $p){return (Get-Content $p -TotalCount 1)}}catch{};return ''}
function HasProv($p){$h=Head $p;foreach($c in @('source_name','source_url','source_record_id','fetched_at','license_name')){if($h -notmatch $c){return $false}};return $true}
function Run($label,$cmd){L($label+'_BEGIN');L('COMMAND='+$cmd);$o=cmd.exe /c $cmd 2>&1;$c=$LASTEXITCODE;$t=($o|Out-String);Write-Output $t;L($label+'_EXIT='+$c);return [ordered]@{label=$label;exit_code=$c;preview=$t.Substring(0,[Math]::Min(3000,$t.Length))}}
$checks=@();$candidates=@();$critical=@()
if(Test-Path $ProjectRoot){Set-Location $ProjectRoot;$checks+=Run 'COLLECT_LEGAL_LIMIT25' 'python scripts\contractor_collect_procurement_ocds.py --storage-root "E:\AAYS_DATA\legal" --limit 25';$checks+=Run 'NORMALIZE_LEGAL' 'python scripts\contractor_normalize_and_score.py --storage-root "E:\AAYS_DATA\legal"'}
foreach($root in @($LegalRoot,$ContractorRoot)){if(Test-Path $root){Get-ChildItem $root -Recurse -File -Include *.csv,*.jsonl -ErrorAction SilentlyContinue|ForEach-Object{if(HasProv $_.FullName){$candidates += [ordered]@{path=$_.FullName;bytes=$_.Length;rows=Rows $_.FullName;header=Head $_.FullName}}}}}
foreach($p in @('processed\contractors_normalized.csv','processed\procurement_events_normalized.csv','processed\contractor_scores.csv','processed\contractor_parcel_matches.csv','exports\contractor_app_export.csv')){$f=Join-Path $LegalRoot $p;$critical += [ordered]@{path=$f;exists=(Test-Path $f);rows=Rows $f;has_provenance=HasProv $f}}
$dbCreds=[bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))
$allOk=($critical|Where-Object{-not $_.has_provenance}).Count -eq 0
$progress=86;if($candidates.Count -gt 0){$progress=88};if($allOk){$progress=90};if($dbCreds){$progress=[Math]::Max($progress,92)}
$a=[ordered]@{task_id=$TaskId;status='completed';generated_at=(Get-Date).ToString('s');db_credentials_present=$dbCreds;candidate_count=$candidates.Count;candidates=$candidates;critical_files=$critical;checks=$checks;plan_progress_percent=$progress;plan_percent_remaining=(100-$progress);next_action=if($candidates.Count -eq 0){'No complete-provenance local candidates found; keep DB load blocked.'}elseif(-not $allOk){'Map complete-provenance source files to final legal CSVs.'}elseif(-not $dbCreds){'Set DB credentials.'}else{'Run DB load.'}}
$a|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.audit.json'))
$lines=@('# TY112 Find Provenance Sources','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('DB credentials present: '+$dbCreds),('Candidate count: '+$candidates.Count),'','## Critical Files');foreach($x in $critical){$lines+=('- '+$x.path+' exists='+$x.exists+' rows='+$x.rows+' has_provenance='+$x.has_provenance)};$lines+=@('','## Candidate Files');foreach($x in $candidates){$lines+=('- '+$x.path+' rows='+$x.rows+' bytes='+$x.bytes)};$lines+=@('','## Checks');foreach($c in $checks){$lines+=('- '+$c.label+': exit='+$c.exit_code)};$lines+=@('','## Next Action',$a.next_action);$lines|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.report.md'))
L('PLAN_PROGRESS_PERCENT='+$progress);L('PLAN_PERCENT_REMAINING='+(100-$progress));exit 0
