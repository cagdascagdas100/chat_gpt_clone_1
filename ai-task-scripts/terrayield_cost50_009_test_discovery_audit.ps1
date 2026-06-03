$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-009-test-discovery-audit-20260512'
$BridgeRoot = Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$CostRoot = 'E:\AAYS_DATA\cost'
$HandoffRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229'
$ProjectRoot = Join-Path $HandoffRoot 'terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ReportDir = Join-Path $CostRoot 'quality_reports'

function Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Exists([string]$Path) { return [bool](Test-Path $Path) }
function Files([string]$Path, [string]$Filter='*', [int]$Limit=200) { try { if (Test-Path $Path) { return @(Get-ChildItem -Path $Path -Filter $Filter -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First $Limit | ForEach-Object { $_.FullName }) } } catch {}; return @() }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

New-Item -ItemType Directory -Force -Path $ResultDir,$ReportDir | Out-Null

Step "TASK=$TaskId"
Step 'MODE=cost50_test_discovery_audit_readonly'
Step "BRIDGE_ROOT=$BridgeRoot"
Step "PROJECT_ROOT=$ProjectRoot"

$testsDir = Join-Path $ProjectRoot 'tests'
$appDir = Join-Path $ProjectRoot 'app'
$checks = [ordered]@{}
$checks.project_root = Exists $ProjectRoot
$checks.tests_dir = Exists $testsDir
$checks.app_dir = Exists $appDir
$checks.requirements = Exists (Join-Path $ProjectRoot 'requirements.txt')
$checks.pyproject = Exists (Join-Path $ProjectRoot 'pyproject.toml')
$checks.app_main = Exists (Join-Path $ProjectRoot 'app\main.py')
$checks.db_models = Exists (Join-Path $ProjectRoot 'app\db\models.py')

Step 'CHECKS_BEGIN'
foreach ($k in $checks.Keys) { Step ($k + '=' + $checks[$k]) }
Step 'CHECKS_END'

$testFiles = Files $ProjectRoot 'test*.py' 200
$specFiles = Files $ProjectRoot '*spec*.py' 100
$allPy = Files $ProjectRoot '*.py' 250

Step ('TEST_FILE_COUNT=' + $testFiles.Count)
Step ('SPEC_FILE_COUNT=' + $specFiles.Count)
Step ('PY_FILE_COUNT=' + $allPy.Count)

$scanText = ''
foreach ($f in @($allPy | Select-Object -First 120)) { $scanText += "`n---FILE:$f---`n" + (ReadText $f) }
$patterns = [ordered]@{
  pytest_token = '(pytest|unittest|TestClient|assert )'
  fastapi_test = '(TestClient|FastAPI|APIRouter)'
  cost_domain = '(cost|Cost|supplier|contractor|postcode|local_authority)'
  db_test = '(Session|database|engine|models|SQLAlchemy|sqlalchemy)'
  fixture_token = '(fixture|mock|monkeypatch|tmp_path)'
}
$patternChecks = [ordered]@{}
Step 'PATTERN_CHECKS_BEGIN'
foreach ($k in $patterns.Keys) {
  $hit = [bool]($scanText -match $patterns[$k])
  $patternChecks[$k] = $hit
  Step ($k + '=' + $hit)
}
Step 'PATTERN_CHECKS_END'

$compileTargets = @($testFiles | Select-Object -First 50)
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
  $compileOutput = 'No test compile targets found.'
}
Step ('TEST_PY_COMPILE_EXIT=' + $compileExit)

$score = 0
$total = 0
foreach ($k in $checks.Keys) { $total++; if ($checks[$k]) { $score++ } }
foreach ($k in $patternChecks.Keys) { $total++; if ($patternChecks[$k]) { $score++ } }
$total++; if ($testFiles.Count -gt 0) { $score++ }
$total++; if ($compileExit -eq 0) { $score++ }
$readiness = if ($total -gt 0) { [int](($score / $total) * 100) } else { 0 }

$gitStatus = ''
try { $gitStatus = git -C $ProjectRoot status --short 2>&1 | Out-String } catch { $gitStatus = 'git_status_error=' + $_.Exception.Message }

$ReportPath = Join-Path $ResultDir "$TaskId.report.md"
$ExternalReportPath = Join-Path $ReportDir "$TaskId.report.md"
$Report = @()
$Report += '# Cost50 Step 009 Test Discovery Audit'
$Report += ''
$Report += "Generated: $(Get-Date -Format s)"
$Report += "Task: $TaskId"
$Report += ''
$Report += '## Scope'
$Report += '- Read-only test discovery and compile smoke selection.'
$Report += '- No test execution, no server start, no DB write.'
$Report += ''
$Report += '## Checks'
foreach ($k in $checks.Keys) { $Report += "- ${k}: $($checks[$k])" }
$Report += ''
$Report += '## Counts'
$Report += "- test files: $($testFiles.Count)"
$Report += "- spec files: $($specFiles.Count)"
$Report += "- python files sampled: $($allPy.Count)"
$Report += ''
$Report += '## Pattern Checks'
foreach ($k in $patternChecks.Keys) { $Report += "- ${k}: $($patternChecks[$k])" }
$Report += ''
$Report += '## Test File Samples'
if ($testFiles.Count -eq 0) { $Report += '- none' } else { $testFiles | Select-Object -First 30 | ForEach-Object { $Report += '- ' + $_ } }
$Report += ''
$Report += '## Compile Smoke'
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
if ($readiness -ge 70) { $Report += '- Proceed to Step 010 selected smoke run planning.' } else { $Report += '- Add/repair test discovery before selected smoke run.' }
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
