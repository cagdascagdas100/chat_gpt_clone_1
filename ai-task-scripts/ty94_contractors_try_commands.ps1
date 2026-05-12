$ErrorActionPreference='Continue'
$TaskId='ty94-contractors-try-commands'
$BridgeRoot='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot='E:\AAYS_DATA\legal'
$OutDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $OutDir,$LegalRoot,(Join-Path $LegalRoot 'raw\procurement'),(Join-Path $LegalRoot 'processed'),(Join-Path $LegalRoot 'exports'),(Join-Path $LegalRoot 'reports') | Out-Null
function L($m){Write-Output ('['+(Get-Date -Format 's')+'] '+$m)}
function Run($label,$cmd){L($label+'_BEGIN');L('COMMAND='+$cmd);$o=cmd.exe /c $cmd 2>&1;$c=$LASTEXITCODE;$t=($o|Out-String);Write-Output $t;L($label+'_EXIT='+$c);return [ordered]@{label=$label;command=$cmd;exit_code=$c;preview=$t.Substring(0,[Math]::Min(6000,$t.Length))}}
function Rows($p){try{if(Test-Path $p){$n=([IO.File]::ReadAllLines($p)).Length;if($n -gt 0){return $n-1}}}catch{};return 0}
function Exists($p){if(Test-Path $p){$i=Get-Item $p;return [ordered]@{path=$p;exists=$true;bytes=$i.Length}};return [ordered]@{path=$p;exists=$false;bytes=0}}
$checks=@();$files=@();$env:AAYS_LEGAL_ROOT=$LegalRoot
if(Test-Path $ProjectRoot){Set-Location $ProjectRoot}else{L 'PROJECT_ROOT_MISSING'}
$cmds=@(
'python scripts\contractor_collect_procurement_ocds.py',
'python scripts\contractor_collect_procurement_ocds.py --limit 10',
'python scripts\contractor_collect_procurement_ocds.py --max-records 10',
'python scripts\contractor_collect_procurement_ocds.py --demo-limit 10',
'python scripts\contractor_collect_procurement_ocds.py --storage-root "E:\AAYS_DATA\legal"',
'python scripts\contractor_collect_procurement_ocds.py --output-root "E:\AAYS_DATA\legal"'
)
$checks += Run 'HELP' 'python scripts\contractor_collect_procurement_ocds.py --help'
foreach($cmd in $cmds){$r=Run ('TRY_'+($checks.Count)) $cmd;$checks+=$r;if((Test-Path (Join-Path $LegalRoot 'raw\procurement\contracts_finder_ocds.jsonl')) -or (Test-Path (Join-Path $LegalRoot 'raw\procurement\find_tender_ocds.jsonl'))){break}}
$checks += Run 'NORMALIZE' 'python scripts\contractor_normalize_and_score.py'
$checks += Run 'EXPORT' 'python scripts\contractor_export_for_app.py'
foreach($p in @('raw\procurement\contracts_finder_ocds.jsonl','raw\procurement\find_tender_ocds.jsonl','processed\contractors_normalized.csv','processed\procurement_events_normalized.csv','processed\contractor_scores.csv','exports\contractor_app_export.csv','exports\contractor_app_export.jsonl')){$files += Exists (Join-Path $LegalRoot $p)}
$score=Rows (Join-Path $LegalRoot 'processed\contractor_scores.csv');$app=Rows (Join-Path $LegalRoot 'exports\contractor_app_export.csv')
$raw=@($files|Where-Object{$_.path -like '*procurement*jsonl' -and $_.exists -and $_.bytes -gt 0}).Count -gt 0
$progress=52;if($raw){$progress=60};if($score -gt 0){$progress=66};if($app -gt 0){$progress=72}
$a=[ordered]@{task_id=$TaskId;status='completed';generated_at=(Get-Date).ToString('s');checks=$checks;files=$files;score_rows=$score;app_rows=$app;plan_progress_percent=$progress;plan_percent_remaining=(100-$progress)}
$a|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.audit.json'))
$lines=@('# Contractor Try Commands','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('Score rows: '+$score),('App rows: '+$app),'','## Checks');foreach($c in $checks){$lines+=('- '+$c.label+': exit='+$c.exit_code)};$lines+=@('','## Files');foreach($f in $files){$lines+=('- '+$f.path+' exists='+$f.exists+' bytes='+$f.bytes)};$lines|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.report.md'))
L('PLAN_PROGRESS_PERCENT='+$progress);L('PLAN_PERCENT_REMAINING='+(100-$progress));exit 0
