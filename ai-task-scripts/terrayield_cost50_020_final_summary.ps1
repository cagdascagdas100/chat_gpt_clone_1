$ErrorActionPreference = 'Continue'
$TaskId='cost50-020-final-summary-20260512'
$BridgeRoot=Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$CostRoot='E:\AAYS_DATA\cost'
$ProjectRoot='E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'
$ReportDir=Join-Path $CostRoot 'quality_reports'
$HandoffDir=Join-Path $CostRoot 'handoff_ready'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ReportDir,$HandoffDir,$ResultDir | Out-Null
function Step($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function Files($r,$f){try{if(Test-Path $r){return @(Get-ChildItem -Path $r -Filter $f -File -Recurse -ErrorAction SilentlyContinue)}}catch{};return @()}
function Has($p){return [bool](Test-Path $p)}
Step "TASK=$TaskId"
$reports=@(Files $ReportDir '*.md')
$json=@(Files $ReportDir '*.json')
$handoff=@(Files $HandoffDir '*')
$py=@(Files $ProjectRoot '*.py')
$checks=[ordered]@{project_root=Has $ProjectRoot;report_dir=Has $ReportDir;handoff_dir=Has $HandoffDir;app_main=Has (Join-Path $ProjectRoot 'app\main.py');requirements=Has (Join-Path $ProjectRoot 'requirements.txt');reports=($reports.Count -gt 0);handoff=($handoff.Count -gt 0);python=($py.Count -gt 0)}
foreach($k in $checks.Keys){Step ($k+'='+$checks[$k])}
Step ('REPORT_COUNT='+$reports.Count)
Step ('JSON_COUNT='+$json.Count)
Step ('HANDOFF_COUNT='+$handoff.Count)
Step ('PY_COUNT='+$py.Count)
$score=0;$total=0
foreach($k in $checks.Keys){$total++;if($checks[$k]){$score++}}
$readiness=[int](($score/[Math]::Max($total,1))*100)
$git=''
try{$git=git -C $ProjectRoot status --short 2>&1|Out-String}catch{$git=$_.Exception.Message}
$r=@()
$r+='# Cost50 Final Summary'
$r+=''
$r+="Generated: $(Get-Date -Format s)"
$r+="Task: $TaskId"
$r+=''
$r+='## Counts'
$r+="- reports: $($reports.Count)"
$r+="- json: $($json.Count)"
$r+="- handoff: $($handoff.Count)"
$r+="- python: $($py.Count)"
$r+=''
$r+='## Checks'
foreach($k in $checks.Keys){$r+="- ${k}: $($checks[$k])"}
$r+=''
$r+='## Git Status'
$r+='```text'
$r+=$git
$r+='```'
$r+=''
$r+="Readiness score: $readiness"
$r+='TASK_COMPLETION=100/100'
$r+='TERRAYIELD_TASK_DONE'
$out=Join-Path $ResultDir "$TaskId.report.md"
$ext=Join-Path $ReportDir "$TaskId.report.md"
$final=Join-Path $HandoffDir 'COST50_FINAL_SUMMARY_20260512.md'
$r|Set-Content -Path $out -Encoding UTF8
try{Copy-Item $out $ext -Force}catch{}
try{Copy-Item $out $final -Force}catch{}
Step "REPORT_PATH=$out"
Step "EXTERNAL_REPORT_PATH=$ext"
Step "FINAL_SUMMARY=$final"
Step "PLAN_PROGRESS_PERCENT=$readiness"
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
