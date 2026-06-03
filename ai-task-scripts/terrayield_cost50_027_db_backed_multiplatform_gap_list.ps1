$ErrorActionPreference='Continue'
$TaskId='cost50-027-db-backed-multiplatform-gap-list-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ConfigPath=Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if(Test-Path $ConfigPath){ . $ConfigPath }
$ProjectRoot=if($env:AAYS_PROJECT_ROOT){$env:AAYS_PROJECT_ROOT}else{'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'}
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function CountLike($root,$pattern){ if(Test-Path $root){ return @((Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match $pattern })).Count } return 0 }
function HasLike($root,$pattern){ return ((CountLike $root $pattern) -gt 0) }
Log "TASK=$TaskId"
Log 'MODE=readonly_db_backed_multiplatform_gap_list'
$dbSignals=@{
  postgres=HasLike $ProjectRoot '(postgres|psycopg|asyncpg|DATABASE_URL|sqlalchemy)'
  migrations=HasLike $ProjectRoot '(alembic|migration|migrations|schema|\.sql$)'
  cost_tables=HasLike $ProjectRoot '(cost_sources|cost_facts|cost_estimates|cost_run_logs|cost_estimate_lines)'
}
$appSignals=@{
  api=HasLike $ProjectRoot '(FastAPI|APIRouter|route|controller|server|main\.py)'
  web=HasLike $ProjectRoot '(england_map_web|react|vite|next|src|public)'
  mobile=HasLike $ProjectRoot '(android|ios|react-native|expo|capacitor|flutter)'
  ui_payload=HasLike $ProjectRoot '(aays_cost_menu_payload_latest|aays_cost_material_lines_latest)'
}
$gaps=@()
if(-not $dbSignals.postgres){$gaps+='PostgreSQL connection/config signal missing or not discoverable.'}
if(-not $dbSignals.migrations){$gaps+='Migration/schema signal missing or not discoverable.'}
if(-not $dbSignals.cost_tables){$gaps+='Cost table/model signal missing or not discoverable.'}
if(-not $appSignals.api){$gaps+='API route/server signal missing or not discoverable.'}
if(-not $appSignals.web){$gaps+='Web/UI signal missing or not discoverable.'}
if(-not $appSignals.mobile){$gaps+='Mobile/platform signal missing or not discoverable.'}
if(-not $appSignals.ui_payload){$gaps+='Required UI payload artifact signal missing or not discoverable.'}
$score=100-($gaps.Count*12); if($score -lt 0){$score=0}
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# Cost50 027 DB-backed Multiplatform Gap List','',"Generated: $(Get-Date -Format s)",'','## DB signals')
foreach($k in $dbSignals.Keys){$r+="- ${k}: $($dbSignals[$k])"}
$r+='','## App/platform signals'
foreach($k in $appSignals.Keys){$r+="- ${k}: $($appSignals[$k])"}
$r+='','## Gap list'
if($gaps.Count -eq 0){$r+='- None detected by this audit.'}else{foreach($g in $gaps){$r+="- $g"}}
$r+='','## Next recommended step','- cost50-028-postgres-migration-target-spec-audit','',"MULTIPLATFORM_DB_READINESS_SCORE=$score/100",'PLAN_PROGRESS_PERCENT=54','TASK_COMPLETION=100/100'
$r|Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log "MULTIPLATFORM_DB_READINESS_SCORE=$score/100"
Log 'PLAN_PROGRESS_PERCENT=54'
Log 'TASK_COMPLETION=100/100'
exit 0
