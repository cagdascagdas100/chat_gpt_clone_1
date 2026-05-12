$ErrorActionPreference='Continue'
$TaskId='cost50-027-gap-list-audit-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function Cnt($root,$pattern){if(Test-Path $root){return @((Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue|Where-Object{$_.FullName -match $pattern})).Count};return 0}
function Has($p){return [bool](Test-Path $p)}
Log "TASK=$TaskId"
$ProjectRoot='E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'
$signals=[ordered]@{
  project_root=Has $ProjectRoot
  requirements=Has (Join-Path $ProjectRoot 'requirements.txt')
  package_json=Has (Join-Path $ProjectRoot 'package.json')
  dockerfile=Has (Join-Path $ProjectRoot 'Dockerfile')
  compose=Has (Join-Path $ProjectRoot 'docker-compose.yml')
  app_main=Has (Join-Path $ProjectRoot 'app\main.py')
  alembic=Has (Join-Path $ProjectRoot 'alembic')
}
$counts=[ordered]@{
  db=Cnt $ProjectRoot '(postgres|pgsql|database|db|schema|alembic)'
  api=Cnt $ProjectRoot '(api|route|controller|server|fastapi)'
  web=Cnt $ProjectRoot '(vite|next|react|src|frontend)'
  mobile=Cnt $ProjectRoot '(android|ios|react-native|expo|capacitor|mobile)'
  tests=Cnt $ProjectRoot '(test|tests|pytest|spec)'
}
foreach($k in $signals.Keys){Log ($k+'='+$signals[$k])}
foreach($k in $counts.Keys){Log ($k+'='+$counts[$k])}
$gaps=@()
if(-not $signals.project_root){$gaps+='project_root_missing'}
if(-not ($signals.requirements -or $signals.package_json)){$gaps+='dependency_manifest_missing'}
if(-not ($signals.dockerfile -or $signals.compose)){$gaps+='runtime_container_config_missing'}
if($counts.db -eq 0){$gaps+='db_schema_signal_missing'}
if($counts.api -eq 0){$gaps+='api_signal_missing'}
if($counts.web -eq 0){$gaps+='web_signal_missing'}
if($counts.tests -eq 0){$gaps+='test_signal_missing'}
$score=[Math]::Max(0,100-($gaps.Count*10))
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# Cost50 027 Gap List Audit','',"Generated: $(Get-Date -Format s)","Task: $TaskId",'','## Signals')
foreach($k in $signals.Keys){$r+="- ${k}: $($signals[$k])"}
$r+=''
$r+='## Counts'
foreach($k in $counts.Keys){$r+="- ${k}: $($counts[$k])"}
$r+=''
$r+='## Gaps'
if($gaps.Count -eq 0){$r+='- none'}else{foreach($g in $gaps){$r+="- $g"}}
$r+=''
$r+="Readiness score: $score"
$r+='PLAN_PROGRESS_PERCENT=54'
$r+='TASK_COMPLETION=100/100'
$r+='TERRAYIELD_TASK_DONE'
$r|Set-Content -Path $out -Encoding UTF8
Log "REPORT_PATH=$out"
Log "READINESS_SCORE=$score"
Log 'PLAN_PROGRESS_PERCENT=54'
Log 'TASK_COMPLETION=100/100'
exit 0
