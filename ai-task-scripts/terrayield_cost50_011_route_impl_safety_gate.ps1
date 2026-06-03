$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-011-route-impl-safety-gate-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function Log([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Exists([string]$Path) { return [bool](Test-Path $Path) }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

Log "TASK=$TaskId"
Log 'MODE=route_impl_safety_gate_readonly'
Log "PROJECT_ROOT=$ProjectRoot"

$mainPath = Join-Path $ProjectRoot 'app\main.py'
$modelPath = Join-Path $ProjectRoot 'app\db\models.py'
$dbDir = Join-Path $ProjectRoot 'app\db'
$appDir = Join-Path $ProjectRoot 'app'
$apiDir = Join-Path $ProjectRoot 'app\api'
$routeCandidate = Join-Path $ProjectRoot 'app\api\cost.py'

$mainText = ReadText $mainPath
$modelText = ReadText $modelPath
$pyFiles = @()
try { if (Exists $appDir) { $pyFiles = Get-ChildItem -Path $appDir -Filter '*.py' -File -Recurse -ErrorAction SilentlyContinue } } catch {}
$combined = ''
foreach ($f in $pyFiles) { $combined += "`n---FILE:$($f.FullName)---`n" + (ReadText $f.FullName) }

$gate = [ordered]@{
  project_root_exists = Exists $ProjectRoot
  main_exists = Exists $mainPath
  db_models_exists = Exists $modelPath
  app_dir_exists = Exists $appDir
  api_dir_exists = Exists $apiDir
  fastapi_app_detected = [bool]($mainText -match 'FastAPI\(')
  include_router_detected = [bool]($mainText -match 'include_router')
  has_apirouter_usage = [bool]($combined -match 'APIRouter')
  cost_route_file_exists = Exists $routeCandidate
  cost_run_logs_model_signal = [bool]($modelText -match 'cost_run_logs|CostRunLog')
  estimate_lines_model_signal = [bool]($modelText -match 'cost_estimate_lines|CostEstimateLine|estimate_lines')
}

Log 'SAFETY_GATE_BEGIN'
foreach ($k in $gate.Keys) { Log ($k + '=' + $gate[$k]) }
Log 'SAFETY_GATE_END'

$blockers = @()
if (-not $gate.project_root_exists) { $blockers += 'Project root missing.' }
if (-not $gate.main_exists) { $blockers += 'app/main.py missing.' }
if (-not $gate.fastapi_app_detected) { $blockers += 'FastAPI app not detected in app/main.py.' }
if (-not $gate.db_models_exists) { $blockers += 'app/db/models.py missing.' }
if (-not $gate.cost_run_logs_model_signal) { $blockers += 'cost_run_logs model signal missing; route error persistence may not be implementable yet.' }
if (-not $gate.estimate_lines_model_signal) { $blockers += 'estimate line model signal missing; itemized cost response persistence may be incomplete.' }

$allowedNext = ($blockers.Count -eq 0)
$score = 0
foreach ($k in $gate.Keys) { if ($gate[$k]) { $score += 8 } }
if ($score -gt 100) { $score = 100 }

$patchTargets = @(
  'app/api/cost.py',
  'app/main.py',
  'app/db/models.py only if missing cost persistence models are confirmed in Step 012'
)

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @()
$report += '# Cost50 Step 011 Route Implementation Safety Gate'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only safety gate before any route implementation patch.'
$report += '- No source mutation, no DB writes, no external fetch.'
$report += ''
$report += '## Gate checks'
foreach ($k in $gate.Keys) { $report += "- ${k}: $($gate[$k])" }
$report += ''
$report += '## Blockers'
if ($blockers.Count -eq 0) { $report += '- None detected by this audit.' } else { foreach ($b in $blockers) { $report += "- $b" } }
$report += ''
$report += '## Candidate patch targets for next implementation step'
foreach ($t in $patchTargets) { $report += "- $t" }
$report += ''
$report += "Safety gate score: $score"
$report += "Implementation allowed next: $allowedNext"
$report += ''
$report += 'PLAN_PROGRESS_PERCENT=22'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

Log ('REPORT_PATH=' + $reportPath)
Log ('SAFETY_GATE_SCORE=' + $score)
Log ('IMPLEMENTATION_ALLOWED_NEXT=' + $allowedNext)
Log 'PLAN_PROGRESS_PERCENT=22'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
