$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-006-schema-migration-draft-audit-20260512'
$BridgeRoot = Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$CostRoot = 'E:\AAYS_DATA\cost'
$HandoffRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229'
$ProjectRoot = Join-Path $HandoffRoot 'terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ReportDir = Join-Path $CostRoot 'quality_reports'

function Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Exists([string]$Path) { return [bool](Test-Path $Path) }
function First-Files([string]$Path, [string]$Filter='*', [int]$Limit=50) { try { if (Test-Path $Path) { return @(Get-ChildItem -Path $Path -Filter $Filter -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First $Limit | ForEach-Object { $_.FullName }) } } catch {}; return @() }
function Read-Small([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

New-Item -ItemType Directory -Force -Path $ResultDir,$ReportDir | Out-Null

Step "TASK=$TaskId"
Step 'MODE=cost50_schema_migration_draft_audit_readonly'
Step "BRIDGE_ROOT=$BridgeRoot"
Step "PROJECT_ROOT=$ProjectRoot"

$modelsPath = Join-Path $ProjectRoot 'app\db\models.py'
$alembicEnv = Join-Path $ProjectRoot 'alembic\env.py'
$alembicVersionsDir = Join-Path $ProjectRoot 'alembic\versions'
$alembicIni = Join-Path $ProjectRoot 'alembic.ini'

$checks = [ordered]@{}
$checks.project_root = Exists $ProjectRoot
$checks.models_py = Exists $modelsPath
$checks.alembic_env = Exists $alembicEnv
$checks.alembic_ini = Exists $alembicIni
$checks.alembic_versions_dir = Exists $alembicVersionsDir
$checks.app_db_dir = Exists (Join-Path $ProjectRoot 'app\db')
$checks.app_main = Exists (Join-Path $ProjectRoot 'app\main.py')

Step 'CHECKS_BEGIN'
foreach ($k in $checks.Keys) { Step ($k + '=' + $checks[$k]) }
Step 'CHECKS_END'

$versionFiles = First-Files $alembicVersionsDir '*.py' 50
$modelText = Read-Small $modelsPath
$alembicText = Read-Small $alembicEnv
$iniText = Read-Small $alembicIni
$combined = $modelText + "`n" + $alembicText + "`n" + $iniText

$patterns = [ordered]@{
  sqlalchemy_model = '(declarative_base|Mapped\[|Column\(|Base\.|metadata)'
  cost_domain = '(cost|Cost|estimate|supplier|contractor|parcel|local_authority|postcode)'
  alembic_target_metadata = 'target_metadata'
  db_url = '(DATABASE_URL|sqlalchemy.url|postgresql|postgres)'
  numeric_money = '(Numeric|DECIMAL|Float|Integer)'
}

$patternChecks = [ordered]@{}
Step 'PATTERN_CHECKS_BEGIN'
foreach ($k in $patterns.Keys) {
  $hit = [bool]($combined -match $patterns[$k])
  $patternChecks[$k] = $hit
  Step ($k + '=' + $hit)
}
Step 'PATTERN_CHECKS_END'

$compileExit = 0
$compileOutput = ''
$compileTargets = @()
if (Exists $modelsPath) { $compileTargets += $modelsPath }
if (Exists $alembicEnv) { $compileTargets += $alembicEnv }
$compileTargets += @($versionFiles | Select-Object -First 20)
$compileTargets = @($compileTargets | Select-Object -Unique)

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
Step ('ALEMBIC_VERSION_COUNT=' + $versionFiles.Count)

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
$Report += '# Cost50 Step 006 Schema Migration Draft Audit'
$Report += ''
$Report += "Generated: $(Get-Date -Format s)"
$Report += "Task: $TaskId"
$Report += ''
$Report += '## Scope'
$Report += '- Read-only schema and Alembic readiness audit.'
$Report += '- No database writes and no migration execution.'
$Report += ''
$Report += '## Checks'
foreach ($k in $checks.Keys) { $Report += "- ${k}: $($checks[$k])" }
$Report += ''
$Report += '## Pattern Checks'
foreach ($k in $patternChecks.Keys) { $Report += "- ${k}: $($patternChecks[$k])" }
$Report += ''
$Report += '## Alembic Version Samples'
if ($versionFiles.Count -eq 0) { $Report += '- none' } else { $versionFiles | Select-Object -First 20 | ForEach-Object { $Report += '- ' + $_ } }
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
if ($readiness -ge 75) { $Report += '- Proceed to Step 007 API/app smoke audit.' } else { $Report += '- Repair schema/Alembic discovery before API/app smoke.' }
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
