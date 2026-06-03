$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-009-route-stub-gap-audit-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function Log([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

Log "TASK=$TaskId"
Log 'MODE=route_stub_gap_audit_readonly'
Log "PROJECT_ROOT=$ProjectRoot"

$pyFiles = @()
try {
  if (Test-Path $ProjectRoot) {
    $pyFiles = Get-ChildItem -Path $ProjectRoot -Filter '*.py' -File -Recurse -ErrorAction SilentlyContinue
  }
} catch {}

$combined = ''
foreach ($f in $pyFiles) { $combined += "`n---FILE:$($f.FullName)---`n" + (ReadText $f.FullName) }

$required = [ordered]@{
  post_admin_cost_sources_sync = 'POST /admin/cost/sources/sync'
  post_admin_cost_estimate = 'POST /admin/cost/estimate'
  get_parcel_cost_latest = 'GET /parcels/{parcel_id}/cost-latest'
  get_parcel_cost_history = 'GET /parcels/{parcel_id}/cost-history'
  get_cost_sources_status = 'GET /cost/sources/status'
}

$patterns = [ordered]@{
  post_admin_cost_sources_sync = 'admin.*/cost.*/sources.*/sync|/admin/cost/sources/sync|cost_sources_sync|sources_sync'
  post_admin_cost_estimate = 'admin.*/cost.*/estimate|/admin/cost/estimate|cost_estimate|estimate_cost'
  get_parcel_cost_latest = 'cost-latest|cost_latest|latest_cost'
  get_parcel_cost_history = 'cost-history|cost_history|history_cost'
  get_cost_sources_status = 'cost.*/sources.*/status|/cost/sources/status|sources_status|cost_sources_status'
}

$routeHits = [ordered]@{}
$missing = @()
Log 'ROUTE_GAP_SCAN_BEGIN'
foreach ($k in $patterns.Keys) {
  $hit = [bool]($combined -match $patterns[$k])
  $routeHits[$k] = $hit
  if (-not $hit) { $missing += $k }
  Log ($k + '=' + $hit + ' required=' + $required[$k])
}
Log 'ROUTE_GAP_SCAN_END'

$moduleSignals = [ordered]@{
  fastapi_router = [bool]($combined -match 'APIRouter|FastAPI')
  pydantic_schema = [bool]($combined -match 'BaseModel|pydantic')
  sqlalchemy_session = [bool]($combined -match 'Session|AsyncSession|sessionmaker')
  run_log_reference = [bool]($combined -match 'cost_run_logs|run_log|logger')
  estimate_line_reference = [bool]($combined -match 'cost_estimate_lines|estimate_lines|line_items|materials')
}

Log 'MODULE_SIGNAL_SCAN_BEGIN'
foreach ($k in $moduleSignals.Keys) { Log ($k + '=' + $moduleSignals[$k]) }
Log 'MODULE_SIGNAL_SCAN_END'

$stubPlan = @()
foreach ($m in $missing) {
  switch ($m) {
    'post_admin_cost_sources_sync' { $stubPlan += 'Add POST /admin/cost/sources/sync route stub with run log creation and source sync status payload.' }
    'post_admin_cost_estimate' { $stubPlan += 'Add POST /admin/cost/estimate route stub returning estimate id, total, confidence, and line placeholders.' }
    'get_parcel_cost_latest' { $stubPlan += 'Add GET /parcels/{parcel_id}/cost-latest read route stub.' }
    'get_parcel_cost_history' { $stubPlan += 'Add GET /parcels/{parcel_id}/cost-history read route stub.' }
    'get_cost_sources_status' { $stubPlan += 'Add GET /cost/sources/status route stub with latest fetch status and fact counts.' }
  }
}
if ($stubPlan.Count -eq 0) { $stubPlan += 'No missing route stubs detected by pattern scan; proceed to implementation conformance audit.' }

$total = $routeHits.Count
$hitCount = 0
foreach ($k in $routeHits.Keys) { if ($routeHits[$k]) { $hitCount++ } }
$routeCoverage = if ($total -gt 0) { [int](($hitCount / $total) * 100) } else { 0 }

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @()
$report += '# Cost50 Step 009 Route Stub Gap Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only route stub gap audit.'
$report += '- No source mutation, no DB writes, no external fetch.'
$report += ''
$report += '## Route hits'
foreach ($k in $routeHits.Keys) { $report += "- ${k}: $($routeHits[$k]) :: $($required[$k])" }
$report += ''
$report += '## Module signals'
foreach ($k in $moduleSignals.Keys) { $report += "- ${k}: $($moduleSignals[$k])" }
$report += ''
$report += '## Stub plan for next step'
foreach ($item in $stubPlan) { $report += "- $item" }
$report += ''
$report += "Route coverage percent: $routeCoverage"
$report += ''
$report += 'PLAN_PROGRESS_PERCENT=18'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

Log ('REPORT_PATH=' + $reportPath)
Log ('ROUTE_COVERAGE_PERCENT=' + $routeCoverage)
Log 'PLAN_PROGRESS_PERCENT=18'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
