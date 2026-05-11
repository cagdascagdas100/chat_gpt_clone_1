$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-007-api-app-smoke-audit-20260512'
$BridgeRoot = Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$CostRoot = 'E:\AAYS_DATA\cost'
$HandoffRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229'
$ProjectRoot = Join-Path $HandoffRoot 'terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ReportDir = Join-Path $CostRoot 'quality_reports'

function Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Exists([string]$Path) { return [bool](Test-Path $Path) }
function Files([string]$Path, [string]$Filter='*', [int]$Limit=80) { try { if (Test-Path $Path) { return @(Get-ChildItem -Path $Path -Filter $Filter -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First $Limit | ForEach-Object { $_.FullName }) } } catch {}; return @() }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

New-Item -ItemType Directory -Force -Path $ResultDir,$ReportDir | Out-Null

Step "TASK=$TaskId"
Step 'MODE=cost50_api_app_smoke_audit_readonly'
Step "BRIDGE_ROOT=$BridgeRoot"
Step "PROJECT_ROOT=$ProjectRoot"

$appMain = Join-Path $ProjectRoot 'app\main.py'
$appDir = Join-Path $ProjectRoot 'app'
$apiDir = Join-Path $ProjectRoot 'app\api'
$testsDir = Join-Path $ProjectRoot 'tests'

$checks = [ordered]@{}
$checks.project_root = Exists $ProjectRoot
$checks.app_dir = Exists $appDir
$checks.app_main = Exists $appMain
$checks.api_dir = Exists $apiDir
$checks.tests_dir = Exists $testsDir
$checks.db_models = Exists (Join-Path $ProjectRoot 'app\db\models.py')
$checks.cost_engine = Exists (Join-Path $ProjectRoot 'tools\cost_uk_real_engine')
$checks.requirements = Exists (Join-Path $ProjectRoot 'requirements.txt')

Step 'CHECKS_BEGIN'
foreach ($k in $checks.Keys) { Step ($k + '=' + $checks[$k]) }
Step 'CHECKS_END'

$pyFiles = Files $ProjectRoot '*.py' 200
$routeFiles = @()
$routeFiles += Files $appDir '*route*.py' 50
$routeFiles += Files $appDir '*router*.py' 50
$routeFiles += Files $appDir '*api*.py' 50
$routeFiles = @($routeFiles | Select-Object -Unique)

$compileTargets = @()
if (Exists $appMain) { $compileTargets += $appMain }
$compileTargets += @($routeFiles | Select-Object -First 30)
$compileTargets = @($compileTargets | Select-Object -Unique)

$compileExit = 0
$compileOutput = ''
if ($compileTargets.Count -gt 0) {
  try {
    Push-Location $ProjectRoot
    $compileOutput = python -m py_compile $compileTargets 2>&1 | Out-String
    $compileExit = $LASTEXITCODE
    Pop-Location
  } catch {
    try { Pop-Location } catch {}
    $compileExit = 999
    $compileOutput = $_.Exception.Message
  }
} else {
  $compileExit = 998
  $compileOutput = 'No compile targets found.'
}
Step ('PY_COMPILE_EXIT=' + $compileExit)

$scanText = ''
foreach ($f in @($pyFiles | Select-Object -First 120)) { $scanText += "`n---FILE:$f---`n" + (ReadText $f) }
$patterns = [ordered]@{
  fastapi = '(FastAPI|APIRouter|@app\.|@router\.)'
  app_import = '(from app|import app|from \.|import )'
  health_route = '(health|status|ping|ready|live)'
  cost_domain = '(cost|Cost|estimate|UK|uk|postcode|local_authority)'
  db_usage = '(Session|database|engine|models|SQLAlchemy|sqlalchemy)'
}
$patternChecks = [ordered]@{}
Step 'PATTERN_CHECKS_BEGIN'
foreach ($k in $patterns.Keys) {
  $hit = [bool]($scanText -match $patterns[$k])
  $patternChecks[$k] = $hit
  Step ($k + '=' + $hit)
}
Step 'PATTERN_CHECKS_END'

$score = 0
$total = 0
foreach ($k in $checks.Keys) { $total++; if ($checks[$k]) { $score++ } }
foreach ($k in $patternChecks.Keys) { $total++; if ($patternChecks[$k]) { $score++ } }
$total++; if ($compileExit -eq 0) { $score++ }
$readiness = if ($total -gt 0) { [int](($score / $total) * 100) } else { 0 }

$gitStatus = ''
try { $gitStatus = git -C $ProjectRoot status --short 2>&1 | Out-String } catch { $gitStatus = 'git_status_error=' + $_.Exception.Message }

$ReportPath = Join-Path $ResultDir "$TaskId.report.md"
$ExternalReportPath = Join-Path $ReportDir "$TaskId.report.md"
$Report = @()
$Report += '# Cost50 Step 007 API App Smoke Audit'
$Report += ''
$Report += "Generated: $(Get-Date -Format s)"
$Report += "Task: $TaskId"
$Report += ''
$Report += '## Scope'
$Report += '- Read-only API/app structure and import smoke audit.'
$Report += '- No server start, no network call, no database write.'
$Report += ''
$Report += '## Checks'
foreach ($k in $checks.Keys) { $Report += "- ${k}: $($checks[$k])" }
$Report += ''
$Report += '## Pattern Checks'
foreach ($k in $patternChecks.Keys) { $Report += "- ${k}: $($patternChecks[$k])" }
$Report += ''
$Report += '## Route/API File Samples'
if ($routeFiles.Count -eq 0) { $Report += '- none' } else { $routeFiles | Select-Object -First 25 | ForEach-Object { $Report += '- ' + $_ } }
$Report += ''
$Report += '## Python Compile'
$Report += "- exit: $compileExit"
$Report += '```text'
$Report += $compileOutput
$Report += '```'
$Report += ''
$Report += '## Git Status'
$Report += '```text'
$Report += $gitStatus
$Report += '```'
$Report += ''
$Report += "Readiness score: $readiness"
$Report += ''
$Report += '## Next Recommendation'
if ($readiness -ge 75) { $Report += '- Proceed to Step 008 data fixture/import audit.' } else { $Report += '- Repair app/API smoke findings before fixture/import audit.' }
$Report += ''
$Report += "PLAN_PROGRESS_PERCENT=$readiness"
$Report += 'TASK_COMPLETION=100/100'
$Report += 'TERRAYIELD_TASK_DONE'

$Report | Set-Content -Path $ReportPath -Encoding UTF8
try { Copy-Item -Path $ReportPath -Destination $ExternalReportPath -Force } catch {}

Step ('REPORT_PATH=' + $ReportPath)
Step ('EXTERNAL_REPORT_PATH=' + $ExternalReportPath)
Step ('PLAN_PROGRESS_PERCENT=' + $readiness)
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
