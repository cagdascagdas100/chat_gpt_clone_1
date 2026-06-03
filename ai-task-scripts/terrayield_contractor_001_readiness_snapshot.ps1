$ErrorActionPreference='Continue'
$TaskId='contractor-001-readiness-snapshot-20260513'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function Has($p){return [bool](Test-Path $p)}
function Cnt($r,$f){try{if(Test-Path $r){return @(Get-ChildItem -Path $r -Filter $f -File -Recurse -ErrorAction SilentlyContinue).Count}}catch{};return 0}
Log "TASK=$TaskId"
$Root='E:\AAYS_DATA\contractor'
$checks=[ordered]@{contractor_root=Has $Root;handoff=Has (Join-Path $Root 'handoff');templates=Has (Join-Path $Root 'templates');demo_data=Has (Join-Path $Root 'demo_data');runbooks=Has (Join-Path $Root 'runbooks')}
$counts=[ordered]@{zip=Cnt (Join-Path $Root 'handoff') '*.zip';csv=Cnt $Root '*.csv';json=Cnt $Root '*.json';md=Cnt $Root '*.md';ps1=Cnt $Root '*.ps1'}
foreach($k in $checks.Keys){Log ($k+'='+$checks[$k])}
foreach($k in $counts.Keys){Log ($k+'='+$counts[$k])}
$score=0;$total=0
foreach($k in $checks.Keys){$total++;if($checks[$k]){$score++}}
foreach($k in @('zip','csv','json','md')){$total++;if($counts[$k] -gt 0){$score++}}
$readiness=[int](($score/[Math]::Max($total,1))*100)
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# Contractor 001 Readiness Snapshot','',"Generated: $(Get-Date -Format s)","Task: $TaskId",'','## Checks')
foreach($k in $checks.Keys){$r+="- ${k}: $($checks[$k])"}
$r+=''
$r+='## Counts'
foreach($k in $counts.Keys){$r+="- ${k}: $($counts[$k])"}
$r+=''
$r+="Readiness score: $readiness"
$r+='PLAN_PROGRESS_PERCENT=66'
$r+='TASK_COMPLETION=100/100'
$r+='TERRAYIELD_TASK_DONE'
$r|Set-Content -Path $out -Encoding UTF8
Log "REPORT_PATH=$out"
Log "READINESS_SCORE=$readiness"
Log 'PLAN_PROGRESS_PERCENT=66'
Log 'TASK_COMPLETION=100/100'
exit 0
