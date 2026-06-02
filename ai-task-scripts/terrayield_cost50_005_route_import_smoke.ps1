$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-005-route-import-smoke-20260512'
$BridgeRoot = Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$CostRoot = 'E:\AAYS_DATA\cost'
$HandoffRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229'
$ProjectRoot = Join-Path $HandoffRoot 'terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ReportDir = Join-Path $CostRoot 'quality_reports'

function Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Exists([string]$Path) { return [bool](Test-Path $Path) }
function Count-Files([string]$Path, [string]$Filter='*') { try { if (Test-Path $Path) { return @(Get-ChildItem -Path $Path -Filter $Filter -File -Recurse -ErrorAction SilentlyContinue).Count } } catch {}; return 0 }
function First-Files([string]$Path, [string]$Filter='*', [int]$Limit=20) { try { if (Test-Path $Path) { return @(Get-ChildItem -Path $Path -Filter $Filter -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First $Limit | ForEach-Object { $_.FullName }) } } catch {}; return @() }

New-Item -ItemType Directory -Force -Path $ResultDir,$ReportDir | Out-Null

Step "TASK=$TaskId"
Step 'MODE=cost50_route_import_smoke_readonly'
Step "BRIDGE_ROOT=$BridgeRoot"
Step "PROJECT_ROOT=$ProjectRoot"

$checks = [ordered]@{}
$checks.project_root = Exists $ProjectRoot
$checks.app_main = Exists (Join-Path $ProjectRoot 'app\main.py')
$checks.app_dir = Exists (Join-Path $ProjectRoot 'app')
$checks.api_dir = Exists (Join-Path $ProjectRoot 'app\api')
$checks.routes_dir = (Exists (Join-Path $ProjectRoot 'app\routes')) -or (Exists (Join-Path $ProjectRoot 'app\api\routes'))
$checks.db_models = Exists (Join-Path $ProjectRoot 'app\db\models.py')
$checks.cost_engine = Exists (Join-Path $ProjectRoot 'tools\cost_uk_real_engine')
$checks.tests_dir = Exists (Join-Path $ProjectRoot 'tests')

Step 'CHECKS_BEGIN'
foreach ($k in $checks.Keys) { Step ($k + '=' + $checks[$k]) }
Step 'CHECKS_END'

$routeFiles = @()
$routeFiles += First-Files (Join-Path $ProjectRoot 'app') '*route*.py' 20
$routeFiles += First-Files (Join-Path $ProjectRoot 'app') '*router*.py' 20
$routeFiles += First-Files (Join-Path $ProjectRoot 'app') '*api*.py' 20
$routeFiles = @($routeFiles | Select-Object -Unique)

$pyFiles = First-Files $ProjectRoot '*.py' 200
$compileTargets = @()
if (Exists (Join-Path $ProjectRoot 'app\main.py')) { $compileTargets += (Join-Path $ProjectRoot 'app\main.py') }
$compileTargets += @($routeFiles | Select-Object -First 20)
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

$patternText = ''
foreach ($f in @($pyFiles | Select-Object -First 80)) { try { $patternText += "`n---FILE:$f---`n" + (Get-Content -Raw -Encoding UTF8 $f -ErrorAction SilentlyContinue) } catch {} }
$patterns = [ordered]@{
  fastapi_token = '(FastAPI|APIRouter|@app\.|@router\.)'
  import_token = '(import |from )'
  cost_token = '(cost|Cost|uk|UK)'
  db_token = '(Session|database|engine|models|SQLAlchemy|sqlalchemy)'
}
$patternChecks = [ordered]@{}
Step 'PATTERN_CHECKS_BEGIN'
foreach ($k in $patterns.Keys) {
  $hit = [bool]($patternText -match $patterns[$k])
  $patternChecks[$k] = $hit
  Step ($k + '=' + $hit)
}
Step 'PATTERN_CHECKS_END'

$score = 0
$total = 0
foreach ($k in $checks.Keys) { $total++; if ($checks[$k]) { $score++ } }
foreach ($k in $patternChecks.Keys) { $total++; if ($patternChecks[$k]) { $score++ } }
if ($compileExit -eq 0) { $score++; $total++ } else { $total++ }
$readiness = if ($total -gt 0) { [int](($score / $total) * 100) } else { 0 }

$gitStatus = ''
try { $gitStatus = git -C $ProjectRoot status --short 2>&1 | Out-String } catch { $gitStatus = 'git_status_error=' + $_.Exception.Message }

$ReportPath = Join-Path $ResultDir "$TaskId.report.md"
$ExternalReportPath = Join-Path $ReportDir "$TaskId.report.md"
$Report = @()
$Report += '# Cost50 Step 005 Route Import Smoke'
$Report += ''
$Report += "Generated: $(Get-Date -Format s)"
$Report += "Task: $TaskId"
$Report += ''
$Report += '## Checks'
foreach ($k in $checks.Keys) { $Report += "- ${k}: $($checks[$k])" }
$Report += ''
$Report += '## Pattern Checks'
foreach ($k in $patternChecks.Keys) { $Report += "- ${k}: $($patternChecks[$k])" }
$Report += ''
$Report += '## Route/API File Samples'
if ($routeFiles.Count -eq 0) { $Report += '- none' } else { $routeFiles | Select-Object -First 20 | ForEach-Object { $Report += '- ' + $_ } }
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
if ($readiness -ge 75) { $Report += '- Proceed to Step 006 schema/migration draft audit.' } else { $Report += '- Repair route/import structure before schema/migration draft.' }
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
