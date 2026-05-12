$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-014-source-facts-template-audit-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$CostRoot = if ($env:AAYS_COST_DATA_ROOT) { $env:AAYS_COST_DATA_ROOT } else { 'E:\AAYS_DATA\cost' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function Log([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

Log "TASK=$TaskId"
Log 'MODE=source_facts_template_schema_audit_readonly'
Log "PROJECT_ROOT=$ProjectRoot"
Log "COST_ROOT=$CostRoot"

$searchRoots = @($ProjectRoot, $CostRoot) | Where-Object { Test-Path $_ }
$templateFiles = @()
foreach ($root in $searchRoots) {
  try {
    $templateFiles += Get-ChildItem -Path $root -Filter 'source_facts_extracted_template.csv' -File -Recurse -ErrorAction SilentlyContinue
    $templateFiles += Get-ChildItem -Path $root -Filter 'source_facts_extracted_*.csv' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20
  } catch {}
}
$templateFiles = $templateFiles | Sort-Object FullName -Unique

$requiredColumns = @(
  'source_id',
  'source_url',
  'source_title',
  'retrieved_at',
  'metric_name',
  'metric_value',
  'metric_unit',
  'geography',
  'effective_date',
  'evidence_text',
  'reliability',
  'correctness',
  'confidence',
  'is_seed'
)

Log 'TEMPLATE_FILES_BEGIN'
Log ('TEMPLATE_FILE_COUNT=' + @($templateFiles).Count)
foreach ($f in $templateFiles) { Log ('FILE=' + $f.FullName) }
Log 'TEMPLATE_FILES_END'

$headerText = ''
if (@($templateFiles).Count -gt 0) {
  try { $headerText = (Get-Content -Path $templateFiles[0].FullName -TotalCount 1 -Encoding UTF8 -ErrorAction SilentlyContinue) } catch {}
}

$columnHits = [ordered]@{}
Log 'REQUIRED_COLUMN_SCAN_BEGIN'
foreach ($c in $requiredColumns) {
  $hit = [bool]($headerText -match [regex]::Escape($c))
  $columnHits[$c] = $hit
  Log ($c + '=' + $hit)
}
Log 'REQUIRED_COLUMN_SCAN_END'

$codeText = ''
try {
  Get-ChildItem -Path $ProjectRoot -Include '*.py','*.sql','*.md' -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    $codeText += "`n---FILE:$($_.FullName)---`n" + (ReadText $_.FullName)
  }
} catch {}

$qualitySignals = [ordered]@{
  evidence_text_required = [bool]($codeText -match 'evidence_text')
  reliability_generated = [bool]($codeText -match 'reliability')
  correctness_generated = [bool]($codeText -match 'correctness')
  seed_penalty = [bool]($codeText -match 'seed.*penalty|penalty.*seed|is_seed')
  official_source_url = [bool]($codeText -match 'source_url|official.*url')
  source_id_required = [bool]($codeText -match 'source_id')
}

Log 'QUALITY_SIGNAL_SCAN_BEGIN'
foreach ($k in $qualitySignals.Keys) { Log ($k + '=' + $qualitySignals[$k]) }
Log 'QUALITY_SIGNAL_SCAN_END'

$missingColumns = @()
foreach ($c in $columnHits.Keys) { if (-not $columnHits[$c]) { $missingColumns += $c } }
$missingSignals = @()
foreach ($k in $qualitySignals.Keys) { if (-not $qualitySignals[$k]) { $missingSignals += $k } }

$total = $columnHits.Count + $qualitySignals.Count
$hitCount = 0
foreach ($c in $columnHits.Keys) { if ($columnHits[$c]) { $hitCount++ } }
foreach ($k in $qualitySignals.Keys) { if ($qualitySignals[$k]) { $hitCount++ } }
$coverage = if ($total -gt 0) { [int](($hitCount / $total) * 100) } else { 0 }

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @()
$report += '# Cost50 Step 014 Source Facts Template Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only source_facts_extracted_template.csv schema audit.'
$report += '- No source mutation, no DB writes, no external fetch.'
$report += ''
$report += '## Template files found'
if (@($templateFiles).Count -eq 0) { $report += '- None found.' } else { foreach ($f in $templateFiles) { $report += "- $($f.FullName)" } }
$report += ''
$report += '## Required column hits'
foreach ($c in $columnHits.Keys) { $report += "- ${c}: $($columnHits[$c])" }
$report += ''
$report += '## Missing columns'
if ($missingColumns.Count -eq 0) { $report += '- None detected.' } else { foreach ($m in $missingColumns) { $report += "- $m" } }
$report += ''
$report += '## Quality rule signals'
foreach ($k in $qualitySignals.Keys) { $report += "- ${k}: $($qualitySignals[$k])" }
$report += ''
$report += '## Missing quality signals'
if ($missingSignals.Count -eq 0) { $report += '- None detected.' } else { foreach ($m in $missingSignals) { $report += "- $m" } }
$report += ''
$report += "Template coverage percent: $coverage"
$report += ''
$report += 'PLAN_PROGRESS_PERCENT=28'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

Log ('REPORT_PATH=' + $reportPath)
Log ('TEMPLATE_COVERAGE_PERCENT=' + $coverage)
Log 'PLAN_PROGRESS_PERCENT=28'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
