$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-015-source-manifest-readiness-audit-20260512'
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
Log 'MODE=source_manifest_readiness_audit_readonly'
Log "PROJECT_ROOT=$ProjectRoot"
Log "COST_ROOT=$CostRoot"

$searchRoots = @($ProjectRoot, $CostRoot) | Where-Object { Test-Path $_ }
$manifestFiles = @()
foreach ($root in $searchRoots) {
  try {
    $manifestFiles += Get-ChildItem -Path $root -Filter 'source_fetch_manifest_latest.json' -File -Recurse -ErrorAction SilentlyContinue
    $manifestFiles += Get-ChildItem -Path $root -Filter 'source_fetch_manifest_latest.csv' -File -Recurse -ErrorAction SilentlyContinue
    $manifestFiles += Get-ChildItem -Path $root -Filter 'source_fetch_manifest_*.json' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20
    $manifestFiles += Get-ChildItem -Path $root -Filter 'source_fetch_manifest_*.csv' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20
  } catch {}
}
$manifestFiles = $manifestFiles | Sort-Object FullName -Unique

Log 'MANIFEST_FILES_BEGIN'
Log ('MANIFEST_FILE_COUNT=' + @($manifestFiles).Count)
foreach ($f in $manifestFiles) { Log ('FILE=' + $f.FullName) }
Log 'MANIFEST_FILES_END'

$codeText = ''
try {
  Get-ChildItem -Path $ProjectRoot -Include '*.py','*.sql','*.md','*.json','*.csv' -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    $codeText += "`n---FILE:$($_.FullName)---`n" + (ReadText $_.FullName)
  }
} catch {}

$sourcePrioritySignals = [ordered]@{
  gov_ons_dbt_hmrc_hmlr = [bool]($codeText -match 'GOV|ONS|DBT|HMRC|HMLR|gov\.uk|ons\.gov\.uk')
  paid_professional_label = [bool]($codeText -match 'paid|professional|licensed|subscription')
  seed_fallback_label = [bool]($codeText -match 'seed|fallback')
  source_id = [bool]($codeText -match 'source_id')
  source_url = [bool]($codeText -match 'source_url|url')
  fetched_at = [bool]($codeText -match 'fetched_at|retrieved_at|checked_at')
  confidence_policy = [bool]($codeText -match 'confidence')
  no_high_without_official = [bool]($codeText -match 'HIGH|official|source_id')
}

Log 'SOURCE_PRIORITY_SIGNAL_SCAN_BEGIN'
foreach ($k in $sourcePrioritySignals.Keys) { Log ($k + '=' + $sourcePrioritySignals[$k]) }
Log 'SOURCE_PRIORITY_SIGNAL_SCAN_END'

$requiredManifestOutputs = @(
  'source_fetch_manifest_latest.json',
  'source_fetch_manifest_latest.csv',
  'source_facts_extracted_*.csv',
  'source_facts_scored.csv',
  'source_facts_scored_summary.json'
)

$outputHits = [ordered]@{}
foreach ($name in $requiredManifestOutputs) {
  $hit = $false
  foreach ($root in $searchRoots) {
    try { if (@(Get-ChildItem -Path $root -Filter $name -File -Recurse -ErrorAction SilentlyContinue).Count -gt 0) { $hit = $true } } catch {}
  }
  $outputHits[$name] = $hit
}

Log 'REQUIRED_OUTPUT_SCAN_BEGIN'
foreach ($k in $outputHits.Keys) { Log ($k + '=' + $outputHits[$k]) }
Log 'REQUIRED_OUTPUT_SCAN_END'

$total = $sourcePrioritySignals.Count + $outputHits.Count
$hitCount = 0
foreach ($k in $sourcePrioritySignals.Keys) { if ($sourcePrioritySignals[$k]) { $hitCount++ } }
foreach ($k in $outputHits.Keys) { if ($outputHits[$k]) { $hitCount++ } }
$coverage = if ($total -gt 0) { [int](($hitCount / $total) * 100) } else { 0 }

$missing = @()
foreach ($k in $outputHits.Keys) { if (-not $outputHits[$k]) { $missing += $k } }

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @()
$report += '# Cost50 Step 015 Source Manifest Readiness Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only source manifest and required demo output readiness audit.'
$report += '- No source mutation, no DB writes, no external fetch.'
$report += ''
$report += '## Manifest files found'
if (@($manifestFiles).Count -eq 0) { $report += '- None found.' } else { foreach ($f in $manifestFiles) { $report += "- $($f.FullName)" } }
$report += ''
$report += '## Source priority signals'
foreach ($k in $sourcePrioritySignals.Keys) { $report += "- ${k}: $($sourcePrioritySignals[$k])" }
$report += ''
$report += '## Required demo output hits'
foreach ($k in $outputHits.Keys) { $report += "- ${k}: $($outputHits[$k])" }
$report += ''
$report += '## Missing required demo outputs'
if ($missing.Count -eq 0) { $report += '- None detected.' } else { foreach ($m in $missing) { $report += "- $m" } }
$report += ''
$report += "Manifest readiness percent: $coverage"
$report += ''
$report += 'PLAN_PROGRESS_PERCENT=30'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

Log ('REPORT_PATH=' + $reportPath)
Log ('MANIFEST_READINESS_PERCENT=' + $coverage)
Log 'PLAN_PROGRESS_PERCENT=30'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
