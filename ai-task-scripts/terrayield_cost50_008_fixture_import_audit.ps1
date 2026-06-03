$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-008-fixture-import-audit-20260512'
$BridgeRoot = Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$CostRoot = 'E:\AAYS_DATA\cost'
$HandoffRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229'
$ProjectRoot = Join-Path $HandoffRoot 'terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ReportDir = Join-Path $CostRoot 'quality_reports'

function Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Exists([string]$Path) { return [bool](Test-Path $Path) }
function Files([string]$Path, [string]$Filter='*', [int]$Limit=100) { try { if (Test-Path $Path) { return @(Get-ChildItem -Path $Path -Filter $Filter -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First $Limit | ForEach-Object { $_.FullName }) } } catch {}; return @() }
function Dirs([string]$Path, [string]$Filter='*', [int]$Limit=100) { try { if (Test-Path $Path) { return @(Get-ChildItem -Path $Path -Filter $Filter -Directory -Recurse -ErrorAction SilentlyContinue | Select-Object -First $Limit | ForEach-Object { $_.FullName }) } } catch {}; return @() }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

New-Item -ItemType Directory -Force -Path $ResultDir,$ReportDir | Out-Null

Step "TASK=$TaskId"
Step 'MODE=cost50_fixture_import_audit_readonly'
Step "BRIDGE_ROOT=$BridgeRoot"
Step "PROJECT_ROOT=$ProjectRoot"

$checks = [ordered]@{}
$checks.project_root = Exists $ProjectRoot
$checks.data_dir = (Exists (Join-Path $ProjectRoot 'data')) -or (Exists (Join-Path $ProjectRoot 'datasets')) -or (Exists (Join-Path $ProjectRoot 'fixtures'))
$checks.scripts_dir = Exists (Join-Path $ProjectRoot 'scripts')
$checks.tools_cost_engine = Exists (Join-Path $ProjectRoot 'tools\cost_uk_real_engine')
$checks.tests_dir = Exists (Join-Path $ProjectRoot 'tests')
$checks.requirements = Exists (Join-Path $ProjectRoot 'requirements.txt')
$checks.app_db_models = Exists (Join-Path $ProjectRoot 'app\db\models.py')

Step 'CHECKS_BEGIN'
foreach ($k in $checks.Keys) { Step ($k + '=' + $checks[$k]) }
Step 'CHECKS_END'

$csvFiles = Files $ProjectRoot '*.csv' 80
$jsonFiles = Files $ProjectRoot '*.json' 80
$parquetFiles = Files $ProjectRoot '*.parquet' 80
$sqlFiles = Files $ProjectRoot '*.sql' 80
$pyFiles = Files $ProjectRoot '*.py' 250
$fixtureDirs = @()
$fixtureDirs += Dirs $ProjectRoot '*fixture*' 20
$fixtureDirs += Dirs $ProjectRoot '*data*' 20
$fixtureDirs += Dirs $ProjectRoot '*import*' 20
$fixtureDirs = @($fixtureDirs | Select-Object -Unique)

Step ('CSV_COUNT=' + $csvFiles.Count)
Step ('JSON_COUNT=' + $jsonFiles.Count)
Step ('PARQUET_COUNT=' + $parquetFiles.Count)
Step ('SQL_COUNT=' + $sqlFiles.Count)
Step ('PY_COUNT=' + $pyFiles.Count)

$scanText = ''
foreach ($f in @($pyFiles | Select-Object -First 120)) { $scanText += "`n---FILE:$f---`n" + (ReadText $f) }
$patterns = [ordered]@{
  import_logic = '(read_csv|csv\.reader|pandas|json\.load|COPY |copy_from|bulk_insert|insert\()'
  cost_domain = '(cost|Cost|supplier|contractor|material|labour|labor|postcode|local_authority)'
  validation_logic = '(validate|schema|pydantic|BaseModel|constraint|quality)'
  db_load_logic = '(Session|engine|database|SQLAlchemy|sqlalchemy|execute\()'
  cli_logic = '(argparse|click|typer|if __name__ == .__main__.)'
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
$total++; if (($csvFiles.Count + $jsonFiles.Count + $parquetFiles.Count + $sqlFiles.Count) -gt 0) { $score++ }
$readiness = if ($total -gt 0) { [int](($score / $total) * 100) } else { 0 }

$gitStatus = ''
try { $gitStatus = git -C $ProjectRoot status --short 2>&1 | Out-String } catch { $gitStatus = 'git_status_error=' + $_.Exception.Message }

$ReportPath = Join-Path $ResultDir "$TaskId.report.md"
$ExternalReportPath = Join-Path $ReportDir "$TaskId.report.md"
$Report = @()
$Report += '# Cost50 Step 008 Fixture Import Audit'
$Report += ''
$Report += "Generated: $(Get-Date -Format s)"
$Report += "Task: $TaskId"
$Report += ''
$Report += '## Scope'
$Report += '- Read-only fixture/import discovery audit.'
$Report += '- No import execution, no DB write, no file mutation.'
$Report += ''
$Report += '## Checks'
foreach ($k in $checks.Keys) { $Report += "- ${k}: $($checks[$k])" }
$Report += ''
$Report += '## Counts'
$Report += "- CSV: $($csvFiles.Count)"
$Report += "- JSON: $($jsonFiles.Count)"
$Report += "- Parquet: $($parquetFiles.Count)"
$Report += "- SQL: $($sqlFiles.Count)"
$Report += "- Python: $($pyFiles.Count)"
$Report += ''
$Report += '## Pattern Checks'
foreach ($k in $patternChecks.Keys) { $Report += "- ${k}: $($patternChecks[$k])" }
$Report += ''
$Report += '## Fixture/Data Directory Samples'
if ($fixtureDirs.Count -eq 0) { $Report += '- none' } else { $fixtureDirs | Select-Object -First 30 | ForEach-Object { $Report += '- ' + $_ } }
$Report += ''
$Report += '## Data File Samples'
$dataSamples = @($csvFiles + $jsonFiles + $parquetFiles + $sqlFiles | Select-Object -First 40)
if ($dataSamples.Count -eq 0) { $Report += '- none' } else { $dataSamples | ForEach-Object { $Report += '- ' + $_ } }
$Report += ''
$Report += '## Git Status'
$Report += '```text'
$Report += $gitStatus
$Report += '```'
$Report += ''
$Report += "Readiness score: $readiness"
$Report += ''
$Report += '## Next Recommendation'
if ($readiness -ge 75) { $Report += '- Proceed to Step 009 test suite discovery and smoke selection.' } else { $Report += '- Create or repair fixture/import mapping before test suite smoke.' }
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
