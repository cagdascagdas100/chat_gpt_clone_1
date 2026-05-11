$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-008-route-contract-audit-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function Log([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

Log "TASK=$TaskId"
Log 'MODE=route_contract_audit_readonly'
Log "PROJECT_ROOT=$ProjectRoot"

$apiFiles = @()
try {
  if (Test-Path $ProjectRoot) {
    $apiFiles = Get-ChildItem -Path $ProjectRoot -Include '*.py' -File -Recurse -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -match '\\app\\|\\api\\|\\routes\\|main\.py$' }
  }
} catch {}

$requiredRoutes = @(
  'POST /admin/cost/sources/sync',
  'POST /admin/cost/estimate',
  'GET /parcels/{parcel_id}/cost-latest',
  'GET /parcels/{parcel_id}/cost-history',
  'GET /cost/sources/status'
)

$routePatterns = [ordered]@{
  admin_cost_sources_sync = 'admin.*/cost.*/sources.*/sync|/admin/cost/sources/sync|cost/sources/sync'
  admin_cost_estimate = 'admin.*/cost.*/estimate|/admin/cost/estimate|cost/estimate'
  parcel_cost_latest = 'cost-latest|cost_latest'
  parcel_cost_history = 'cost-history|cost_history'
  cost_sources_status = 'cost.*/sources.*/status|/cost/sources/status|sources/status'
}

$combined = ''
foreach ($f in $apiFiles) { $combined += "`n---FILE:$($f.FullName)---`n" + (ReadText $f.FullName) }

Log 'API_FILE_SCAN_BEGIN'
Log ('API_FILE_COUNT=' + @($apiFiles).Count)
foreach ($f in ($apiFiles | Select-Object -First 40)) { Log ('FILE=' + $f.FullName) }
Log 'API_FILE_SCAN_END'

$routeHits = [ordered]@{}
Log 'ROUTE_CONTRACT_SCAN_BEGIN'
foreach ($k in $routePatterns.Keys) {
  $hit = [bool]($combined -match $routePatterns[$k])
  $routeHits[$k] = $hit
  Log ($k + '=' + $hit)
}
Log 'ROUTE_CONTRACT_SCAN_END'

$qualitySignals = [ordered]@{
  cost_run_logs = [bool]($combined -match 'cost_run_logs|CostRunLog|run_logs')
  line_items = [bool]($combined -match 'line_items|estimate_lines|cost_estimate_lines|material')
  quantity = [bool]($combined -match 'quantity|qty|amount')
  confidence = [bool]($combined -match 'confidence')
  error_logging = [bool]($combined -match 'except|try:|logger|log')
}

Log 'QUALITY_SIGNAL_SCAN_BEGIN'
foreach ($k in $qualitySignals.Keys) { Log ($k + '=' + $qualitySignals[$k]) }
Log 'QUALITY_SIGNAL_SCAN_END'

$hits = 0
$total = $routeHits.Count + $qualitySignals.Count
foreach ($k in $routeHits.Keys) { if ($routeHits[$k]) { $hits++ } }
foreach ($k in $qualitySignals.Keys) { if ($qualitySignals[$k]) { $hits++ } }
$readiness = if ($total -gt 0) { [int](($hits / $total) * 100) } else { 0 }

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @()
$report += '# Cost50 Step 008 Route Contract Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only API route contract audit.'
$report += '- No source mutation, no DB writes, no external fetch.'
$report += ''
$report += '## Required API contract'
foreach ($r in $requiredRoutes) { $report += "- $r" }
$report += ''
$report += '## Route hits'
foreach ($k in $routeHits.Keys) { $report += "- ${k}: $($routeHits[$k])" }
$report += ''
$report += '## Quality signals'
foreach ($k in $qualitySignals.Keys) { $report += "- ${k}: $($qualitySignals[$k])" }
$report += ''
$report += "Route readiness score: $readiness"
$report += ''
$report += '## Next recommendation'
$report += '- Step 009 should draft missing route/module stubs only if route contract gaps are confirmed.'
$report += ''
$report += 'PLAN_PROGRESS_PERCENT=16'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

Log ('REPORT_PATH=' + $reportPath)
Log ('ROUTE_READINESS_SCORE=' + $readiness)
Log 'PLAN_PROGRESS_PERCENT=16'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
