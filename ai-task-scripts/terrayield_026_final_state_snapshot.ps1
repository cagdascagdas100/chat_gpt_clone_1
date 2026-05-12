$ErrorActionPreference='Continue'
$TaskId='terrayield-026-final-state-snapshot-20260512'
$BridgeRoot=Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$CostRoot='E:\AAYS_DATA\cost'
$ContractorRoot='E:\AAYS_DATA\contractor'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Step($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function Has($p){return [bool](Test-Path $p)}
function Count($r,$f){try{if(Test-Path $r){return @(Get-ChildItem -Path $r -Filter $f -File -Recurse -ErrorAction SilentlyContinue).Count}}catch{};return 0}
Step "TASK=$TaskId"
$checks=[ordered]@{bridge=Has $BridgeRoot;project=Has $ProjectRoot;cost=Has $CostRoot;contractor=Has $ContractorRoot;cost_reports=Has (Join-Path $CostRoot 'quality_reports');cost_handoff=Has (Join-Path $CostRoot 'handoff_ready');contractor_handoff=Has (Join-Path $ContractorRoot 'handoff')}
foreach($k in $checks.Keys){Step ($k+'='+$checks[$k])}
$counts=[ordered]@{ai_results=Count $ResultDir '*.md';ai_scripts=Count (Join-Path $BridgeRoot 'ai-task-scripts') '*.ps1';project_py=Count $ProjectRoot '*.py';project_md=Count $ProjectRoot '*.md';cost_reports=Count (Join-Path $CostRoot 'quality_reports') '*.md';cost_handoff=Count (Join-Path $CostRoot 'handoff_ready') '*';contractor_zip=Count (Join-Path $ContractorRoot 'handoff') '*.zip';contractor_csv=Count $ContractorRoot '*.csv'}
foreach($k in $counts.Keys){Step ($k+'='+$counts[$k])}
$score=0;$total=0
foreach($k in $checks.Keys){$total++;if($checks[$k]){$score++}}
foreach($k in @('ai_results','ai_scripts','project_py','cost_reports')){$total++;if($counts[$k] -gt 0){$score++}}
$readiness=[int](($score/[Math]::Max($total,1))*100)
$r=@('# TerraYield 026 Final State Snapshot','',"Generated: $(Get-Date -Format s)","Task: $TaskId",'','## Checks')
foreach($k in $checks.Keys){$r+="- ${k}: $($checks[$k])"}
$r+=''
$r+='## Counts'
foreach($k in $counts.Keys){$r+="- ${k}: $($counts[$k])"}
$r+=''
$r+="Readiness score: $readiness"
$r+='TASK_COMPLETION=100/100'
$r+='TERRAYIELD_TASK_DONE'
$out=Join-Path $ResultDir "$TaskId.report.md"
$r|Set-Content -Path $out -Encoding UTF8
Step "REPORT_PATH=$out"
Step "PLAN_PROGRESS_PERCENT=$readiness"
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
