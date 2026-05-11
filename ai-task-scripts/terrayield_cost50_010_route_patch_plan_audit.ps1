$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-010-route-patch-plan-audit-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function Log([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

Log "TASK=$TaskId"
Log 'MODE=route_patch_plan_audit_readonly'
Log "PROJECT_ROOT=$ProjectRoot"

$mainPath = Join-Path $ProjectRoot 'app\main.py'
$modelPath = Join-Path $ProjectRoot 'app\db\models.py'
$appDir = Join-Path $ProjectRoot 'app'

$pyFiles = @()
try { if (Test-Path $appDir) { $pyFiles = Get-ChildItem -Path $appDir -Filter '*.py' -File -Recurse -ErrorAction SilentlyContinue } } catch {}
$combined = ''
foreach ($f in $pyFiles) { $combined += "`n---FILE:$($f.FullName)---`n" + (ReadText $f.FullName) }

$observed = [ordered]@{
  app_main_exists = Test-Path $mainPath
  db_models_exists = Test-Path $modelPath
  has_fastapi_app = [bool]($combined -match 'FastAPI\(')
  has_api_router = [bool]($combined -match 'APIRouter')
  has_include_router = [bool]($combined -match 'include_router')
  has_cost_route_module = [bool]($combined -match 'cost.*router|router.*cost|cost_routes')
  has_cost_run_logs_model = [bool]($combined -match 'cost_run_logs|CostRunLog')
}

Log 'OBSERVED_BEGIN'
foreach ($k in $observed.Keys) { Log ($k + '=' + $observed[$k]) }
Log 'OBSERVED_END'

$requiredEndpoints = @(
  'POST /admin/cost/sources/sync',
  'POST /admin/cost/estimate',
  'GET /parcels/{parcel_id}/cost-latest',
  'GET /parcels/{parcel_id}/cost-history',
  'GET /cost/sources/status'
)

$patchPlan = @()
if (-not $observed.has_api_router) { $patchPlan += 'Create app/api/cost.py with APIRouter-based route declarations.' }
if (-not $observed.has_include_router) { $patchPlan += 'Patch app/main.py to include the cost router.' }
if (-not $observed.has_cost_run_logs_model) { $patchPlan += 'Ensure DB layer contains cost_run_logs before implementation uses persistent error logging.' }
$patchPlan += 'Route stubs must return explicit placeholder status and must not use fake official source facts.'
$patchPlan += 'POST /admin/cost/estimate response contract must include itemized cost lines and material quantities.'
$patchPlan += 'All exception paths should write a cost_run_logs record once persistence is available.'

Log 'PATCH_PLAN_BEGIN'
foreach ($item in $patchPlan) { Log ('PLAN=' + $item) }
Log 'PATCH_PLAN_END'

$readiness = 0
foreach ($k in $observed.Keys) { if ($observed[$k]) { $readiness += 10 } }
if ($readiness -gt 100) { $readiness = 100 }

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @()
$report += '# Cost50 Step 010 Route Patch Plan Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only implementation patch planning.'
$report += '- No source mutation, no DB writes, no external fetch.'
$report += ''
$report += '## Required endpoints'
foreach ($e in $requiredEndpoints) { $report += "- $e" }
$report += ''
$report += '## Observed signals'
foreach ($k in $observed.Keys) { $report += "- ${k}: $($observed[$k])" }
$report += ''
$report += '## Proposed patch plan for next step'
foreach ($item in $patchPlan) { $report += "- $item" }
$report += ''
$report += "Implementation readiness score: $readiness"
$report += ''
$report += 'PLAN_PROGRESS_PERCENT=20'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

Log ('REPORT_PATH=' + $reportPath)
Log ('IMPLEMENTATION_READINESS_SCORE=' + $readiness)
Log 'PLAN_PROGRESS_PERCENT=20'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
