$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-010-smoke-plan-audit-20260512'
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
Step 'MODE=cost50_smoke_plan_audit_readonly'
Step "BRIDGE_ROOT=$BridgeRoot"
Step "PROJECT_ROOT=$ProjectRoot"

$checks = [ordered]@{}
$checks.project_root = Exists $ProjectRoot
$checks.app_main = Exists (Join-Path $ProjectRoot 'app\main.py')
$checks.tests_dir = Exists (Join-Path $ProjectRoot 'tests')
$checks.requirements = Exists (Join-Path $ProjectRoot 'requirements.txt')
$checks.pyproject = Exists (Join-Path $ProjectRoot 'pyproject.toml')
$checks.db_models = Exists (Join-Path $ProjectRoot 'app\db\models.py')
$checks.alembic_versions = Exists (Join-Path $ProjectRoot 'alembic\versions')
$checks.cost_engine = Exists (Join-Path $ProjectRoot 'tools\cost_uk_real_engine')

Step 'CHECKS_BEGIN'
foreach ($k in $checks.Keys) { Step ($k + '=' + $checks[$k]) }
Step 'CHECKS_END'

$allPy = Files $ProjectRoot '*.py' 300
$testFiles = Files $ProjectRoot 'test*.py' 120
$appMain = Join-Path $ProjectRoot 'app\main.py'
$models = Join-Path $ProjectRoot 'app\db\models.py'
$routeFiles = @()
$routeFiles += Files (Join-Path $ProjectRoot 'app') '*route*.py' 80
$routeFiles += Files (Join-Path $ProjectRoot 'app') '*router*.py' 80
$routeFiles += Files (Join-Path $ProjectRoot 'app') '*api*.py' 80
$routeFiles = @($routeFiles | Select-Object -Unique)

$recommended = New-Object System.Collections.Generic.List[string]
if (Exists $appMain) { $recommended.Add($appMain) | Out-Null }
if (Exists $models) { $recommended.Add($models) | Out-Null }
foreach ($f in @($routeFiles | Select-Object -First 10)) { $recommended.Add($f) | Out-Null }
foreach ($f in @($testFiles | Select-Object -First 20)) { $recommended.Add($f) | Out-Null }
$recommendedList = @($recommended | Select-Object -Unique)

$compileExit = 0
$compileOutput = ''
if ($recommendedList.Count -gt 0) {
  try {
    Push-Location $ProjectRoot
    $compileOutput = python -m py_compile $recommendedList 2>&1 | Out-String
    $compileExit = $LASTEXITCODE
    Pop-Location
  } catch {
    try { Pop-Location } catch {}
    $compileExit = 999
    $compileOutput = $_.Exception.Message
  }
} else {
  $compileExit = 998
  $compileOutput = 'No smoke compile targets found.'
}
Step ('SMOKE_COMPILE_EXIT=' + $compileExit)
Step ('RECOMMENDED_TARGET_COUNT=' + $recommendedList.Count)

$scanText = ''
foreach ($f in @($allPy | Select-Object -First 160)) { $scanText += "`n---FILE:$f---`n" + (ReadText $f) }
$patterns = [ordered]@{
  fastapi = '(FastAPI|APIRouter|TestClient)'
  db = '(SQLAlchemy|sqlalchemy|Session|engine|models|database)'
  alembic = '(alembic|target_metadata|revision|upgrade\(|downgrade\()'
  cost_domain = '(cost|Cost|supplier|contractor|postcode|local_authority|estimate)'
  tests = '(pytest|unittest|assert |fixture|mock)'
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
$total++; if ($recommendedList.Count -gt 0) { $score++ }
$readiness = if ($total -gt 0) { [int](($score / $total) * 100) } else { 0 }

$gitStatus = ''
try { $gitStatus = git -C $ProjectRoot status --short 2>&1 | Out-String } catch { $gitStatus = 'git_status_error=' + $_.Exception.Message }

$ReportPath = Join-Path $ResultDir "$TaskId.report.md"
$ExternalReportPath = Join-Path $ReportDir "$TaskId.report.md"
$Report = @()
$Report += '# Cost50 Step 010 Smoke Plan Audit'
$Report += ''
$Report += "Generated: $(Get-Date -Format s)"
$Report += "Task: $TaskId"
$Report += ''
$Report += '## Scope'
$Report += '- Read-only smoke plan selection and compile check.'
$Report += '- No live server, no DB write, no external network call.'
$Report += ''
$Report += '## Checks'
foreach ($k in $checks.Keys) { $Report += "- ${k}: $($checks[$k])" }
$Report += ''
$Report += '## Pattern Checks'
foreach ($k in $patternChecks.Keys) { $Report += "- ${k}: $($patternChecks[$k])" }
$Report += ''
$Report += '## Recommended Smoke Targets'
if ($recommendedList.Count -eq 0) { $Report += '- none' } else { $recommendedList | Select-Object -First 40 | ForEach-Object { $Report += '- ' + $_ } }
$Report += ''
$Report += '## Compile Result'
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
if ($readiness -ge 75) { $Report += '- Proceed to Step 011 selected smoke execution if allowed.' } else { $Report += '- Resolve smoke target gaps before selected execution.' }
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
