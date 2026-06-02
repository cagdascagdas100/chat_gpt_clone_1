$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-011-selected-smoke-collection-audit-20260512'
$BridgeRoot = Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$CostRoot = 'E:\AAYS_DATA\cost'
$HandoffRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229'
$ProjectRoot = Join-Path $HandoffRoot 'terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ReportDir = Join-Path $CostRoot 'quality_reports'

function Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Exists([string]$Path) { return [bool](Test-Path $Path) }
function Files([string]$Path, [string]$Filter='*', [int]$Limit=300) { try { if (Test-Path $Path) { return @(Get-ChildItem -Path $Path -Filter $Filter -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First $Limit | ForEach-Object { $_.FullName }) } } catch {}; return @() }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

New-Item -ItemType Directory -Force -Path $ResultDir,$ReportDir | Out-Null

Step "TASK=$TaskId"
Step 'MODE=cost50_selected_smoke_collection_audit_readonly'
Step "BRIDGE_ROOT=$BridgeRoot"
Step "PROJECT_ROOT=$ProjectRoot"

$testsDir = Join-Path $ProjectRoot 'tests'
$appMain = Join-Path $ProjectRoot 'app\main.py'
$models = Join-Path $ProjectRoot 'app\db\models.py'
$requirements = Join-Path $ProjectRoot 'requirements.txt'
$pyproject = Join-Path $ProjectRoot 'pyproject.toml'

$checks = [ordered]@{}
$checks.project_root = Exists $ProjectRoot
$checks.tests_dir = Exists $testsDir
$checks.app_main = Exists $appMain
$checks.db_models = Exists $models
$checks.requirements = Exists $requirements
$checks.pyproject = Exists $pyproject
$checks.python_available = $false
$checks.pytest_available = $false

try { $pythonVersion = python --version 2>&1 | Out-String; $checks.python_available = $true } catch { $pythonVersion = 'python check error=' + $_.Exception.Message }
try { $pytestVersion = python -m pytest --version 2>&1 | Out-String; if ($LASTEXITCODE -eq 0) { $checks.pytest_available = $true } } catch { $pytestVersion = 'pytest check error=' + $_.Exception.Message }

Step ('PYTHON_VERSION=' + $pythonVersion.Trim())
Step ('PYTEST_VERSION=' + $pytestVersion.Trim())
Step 'CHECKS_BEGIN'
foreach ($k in $checks.Keys) { Step ($k + '=' + $checks[$k]) }
Step 'CHECKS_END'

$testFiles = Files $ProjectRoot 'test*.py' 150
$allPy = Files $ProjectRoot '*.py' 300
$routeFiles = @()
$routeFiles += Files (Join-Path $ProjectRoot 'app') '*route*.py' 60
$routeFiles += Files (Join-Path $ProjectRoot 'app') '*router*.py' 60
$routeFiles += Files (Join-Path $ProjectRoot 'app') '*api*.py' 60
$routeFiles = @($routeFiles | Select-Object -Unique)

$compileTargets = New-Object System.Collections.Generic.List[string]
if (Exists $appMain) { $compileTargets.Add($appMain) | Out-Null }
if (Exists $models) { $compileTargets.Add($models) | Out-Null }
foreach ($f in @($routeFiles | Select-Object -First 15)) { $compileTargets.Add($f) | Out-Null }
foreach ($f in @($testFiles | Select-Object -First 30)) { $compileTargets.Add($f) | Out-Null }
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
Step ('SELECTED_COMPILE_EXIT=' + $compileExit)

$collectExit = 998
$collectOutput = 'pytest not attempted.'
if ($checks.pytest_available -and (Exists $testsDir)) {
  try {
    Push-Location $ProjectRoot
    $collectOutput = python -m pytest --collect-only -q 2>&1 | Out-String
    $collectExit = $LASTEXITCODE
    Pop-Location
  } catch {
    try { Pop-Location } catch {}
    $collectExit = 999
    $collectOutput = $_.Exception.Message
  }
} elseif (-not $checks.pytest_available) {
  $collectOutput = 'pytest unavailable.'
} elseif (-not (Exists $testsDir)) {
  $collectOutput = 'tests directory missing.'
}
Step ('PYTEST_COLLECT_EXIT=' + $collectExit)

$scanText = ''
foreach ($f in @($allPy | Select-Object -First 160)) { $scanText += "`n---FILE:$f---`n" + (ReadText $f) }
$patterns = [ordered]@{
  tests = '(pytest|unittest|assert |fixture|TestClient)'
  app = '(FastAPI|APIRouter|app =|include_router)'
  db = '(SQLAlchemy|sqlalchemy|Session|engine|models|database)'
  cost = '(cost|Cost|supplier|contractor|postcode|local_authority|estimate)'
  cli = '(argparse|click|typer|__main__)'
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
$total++; if ($collectExit -eq 0 -or $collectExit -eq 5) { $score++ }
$readiness = if ($total -gt 0) { [int](($score / $total) * 100) } else { 0 }

$gitStatus = ''
try { $gitStatus = git -C $ProjectRoot status --short 2>&1 | Out-String } catch { $gitStatus = 'git_status_error=' + $_.Exception.Message }

$ReportPath = Join-Path $ResultDir "$TaskId.report.md"
$ExternalReportPath = Join-Path $ReportDir "$TaskId.report.md"
$Report = @()
$Report += '# Cost50 Step 011 Selected Smoke Collection Audit'
$Report += ''
$Report += "Generated: $(Get-Date -Format s)"
$Report += "Task: $TaskId"
$Report += ''
$Report += '## Scope'
$Report += '- Read-only selected smoke collection audit.'
$Report += '- Runs python compile and pytest collect-only when available.'
$Report += '- No app server start, no database write, no external network call.'
$Report += ''
$Report += '## Checks'
foreach ($k in $checks.Keys) { $Report += "- ${k}: $($checks[$k])" }
$Report += ''
$Report += '## Pattern Checks'
foreach ($k in $patternChecks.Keys) { $Report += "- ${k}: $($patternChecks[$k])" }
$Report += ''
$Report += '## Selected Compile Targets'
if ($compileTargets.Count -eq 0) { $Report += '- none' } else { $compileTargets | Select-Object -First 60 | ForEach-Object { $Report += '- ' + $_ } }
$Report += ''
$Report += '## Python Compile Result'
$Report += "- exit: $compileExit"
$Report += '```text'
$Report += $compileOutput
$Report += '```'
$Report += ''
$Report += '## Pytest Collect Result'
$Report += "- exit: $collectExit"
$Report += '```text'
$Report += $collectOutput
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
if ($readiness -ge 75) { $Report += '- Proceed to Step 012 packaging/readiness closure audit.' } else { $Report += '- Repair selected smoke collection gaps before closure audit.' }
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
