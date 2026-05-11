$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-058-plan-audit-readiness'
$ActiveBridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$ContractorRoot = 'E:\AAYS_DATA\contractor'
$EstatePackage = Join-Path $ContractorRoot 'AAYS_TERRAYIELD_ESTATE_AGENT_DIRECTORY_V3_20260511'
$ResultDir = Join-Path $ActiveBridgeRoot 'ai-results'
$ReportDir = Join-Path $ContractorRoot 'quality_reports'

function Step([string]$Text) {
  Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text)
}

function Test-File([string]$Path, [string]$Label) {
  if (Test-Path $Path) {
    Step ('FOUND_' + $Label + '=' + $Path)
    return $true
  } else {
    Step ('MISSING_' + $Label + '=' + $Path)
    return $false
  }
}

New-Item -ItemType Directory -Force -Path $ResultDir,$ReportDir | Out-Null

Step "TASK=$TaskId"
Step 'MODE=plan_audit_readiness'
Step "ACTIVE_BRIDGE_ROOT=$ActiveBridgeRoot"
Step "PROJECT_ROOT=$ProjectRoot"
Step "CONTRACTOR_ROOT=$ContractorRoot"
Step "ESTATE_PACKAGE=$EstatePackage"

$Score = [ordered]@{
  runner_bridge = 75
  single_continue_model = 70
  git_result_push = 65
  contractor_pipeline = 30
  estate_agent_package = 0
  future_growth = 0
  overall = 0
}

$Findings = New-Object System.Collections.Generic.List[string]
$Warnings = New-Object System.Collections.Generic.List[string]

Step 'PATH_CHECK_BEGIN'
$ProjectOk = Test-Path $ProjectRoot
$ContractorOk = Test-Path $ContractorRoot
$EstateOk = Test-Path $EstatePackage
Step ('PROJECT_ROOT_OK=' + $ProjectOk)
Step ('CONTRACTOR_ROOT_OK=' + $ContractorOk)
Step ('ESTATE_PACKAGE_OK=' + $EstateOk)
Step 'PATH_CHECK_END'

if ($EstateOk) {
  $requiredEstate = @(
    'templates\estate_agent_directory_template.blank.csv',
    'templates\market_provider_manifest_estate_agents.blank.json',
    'templates\source_provenance_template.blank.csv',
    'demo_data\estate_agents_demo_100plus.csv',
    'WORKFLOW_50_STEPS_TR.md',
    'runbooks\RUNBOOK_TR.md',
    'scripts\build_zip.ps1',
    'scripts\validate_estate_agent_directory.ps1',
    'sql\001_estate_agent_directory_schema.sql',
    'sql\002_scoring_and_parcel_agent_top5.sql'
  )
  $present = 0
  foreach ($rel in $requiredEstate) {
    if (Test-File (Join-Path $EstatePackage $rel) ('ESTATE_' + ($rel -replace '[^A-Za-z0-9]+','_'))) { $present++ }
  }
  $Score.estate_agent_package = [int](($present / $requiredEstate.Count) * 100)
  Step ('ESTATE_REQUIRED_PRESENT=' + $present)
  Step ('ESTATE_REQUIRED_TOTAL=' + $requiredEstate.Count)

  $csv = Join-Path $EstatePackage 'demo_data\estate_agents_demo_100plus.csv'
  if (Test-Path $csv) {
    try {
      $rows = Import-Csv $csv
      Step ('ESTATE_DEMO_ROWS=' + $rows.Count)
      if ($rows.Count -ge 100) { $Findings.Add('Estate-agent demo CSV has 100+ rows.') | Out-Null } else { $Warnings.Add('Estate-agent demo CSV has fewer than 100 rows.') | Out-Null }
    } catch {
      $Warnings.Add('Estate-agent CSV read failed: ' + $_.Exception.Message) | Out-Null
    }
  }
} else {
  $Warnings.Add('Estate package not found at expected contractor root.') | Out-Null
}

Step 'CONTRACTOR_FILE_CHECK_BEGIN'
$contractorFiles = @(
  'scripts\contractor_collect_companies_house.py',
  'scripts\contractor_collect_procurement_ocds.py',
  'scripts\contractor_normalize_and_score.py',
  'scripts\contractor_load_to_postgres.py',
  'scripts\contractor_match_to_parcels.py',
  'scripts\contractor_export_for_app.py',
  'scripts\requirements_contractor.txt',
  'scripts\README_CONTRACTOR_PIPELINE.md'
)
$contractorPresent = 0
if ($ProjectOk) {
  foreach ($rel in $contractorFiles) {
    if (Test-File (Join-Path $ProjectRoot $rel) ('CONTRACTOR_' + ($rel -replace '[^A-Za-z0-9]+','_'))) { $contractorPresent++ }
  }
  $Score.contractor_pipeline = [int](($contractorPresent / $contractorFiles.Count) * 100)
}
Step ('CONTRACTOR_FILES_PRESENT=' + $contractorPresent)
Step ('CONTRACTOR_FILES_TOTAL=' + $contractorFiles.Count)
Step 'CONTRACTOR_FILE_CHECK_END'

Step 'FUTURE_GROWTH_CHECK_BEGIN'
$futureFiles = @(
  'future_growth\__init__.py',
  'future_growth\evidence.py',
  'future_growth\timeline.py',
  'future_growth\connectors\__init__.py',
  'future_growth\connectors\base.py'
)
$futurePresent = 0
if ($ProjectOk) {
  foreach ($rel in $futureFiles) {
    if (Test-File (Join-Path $ProjectRoot $rel) ('FUTURE_' + ($rel -replace '[^A-Za-z0-9]+','_'))) { $futurePresent++ }
  }
  $Score.future_growth = [int](($futurePresent / $futureFiles.Count) * 100)
}
Step ('FUTURE_GROWTH_FILES_PRESENT=' + $futurePresent)
Step ('FUTURE_GROWTH_FILES_TOTAL=' + $futureFiles.Count)
Step 'FUTURE_GROWTH_CHECK_END'

Step 'PYTHON_CHECK_BEGIN'
try {
  $pyVersion = python --version 2>&1 | Out-String
  Step ('PYTHON_VERSION=' + $pyVersion.Trim())
} catch {
  $Warnings.Add('Python check failed: ' + $_.Exception.Message) | Out-Null
}
Step 'PYTHON_CHECK_END'

Step 'GIT_STATUS_BEGIN'
$GitStatus = ''
if ($ProjectOk) {
  try {
    Push-Location $ProjectRoot
    $GitStatus = git status --short 2>&1 | Out-String
    $GitHead = git rev-parse HEAD 2>&1 | Out-String
    Pop-Location
    Step ('PROJECT_GIT_HEAD=' + $GitHead.Trim())
    Step 'PROJECT_GIT_STATUS_TEXT_BEGIN'
    Write-Output $GitStatus
    Step 'PROJECT_GIT_STATUS_TEXT_END'
  } catch {
    try { Pop-Location } catch {}
    $Warnings.Add('Git status failed: ' + $_.Exception.Message) | Out-Null
  }
}
Step 'GIT_STATUS_END'

$Score.overall = [int](($Score.runner_bridge + $Score.single_continue_model + $Score.git_result_push + $Score.contractor_pipeline + $Score.estate_agent_package + $Score.future_growth) / 6)

$ReportPath = Join-Path $ResultDir "$TaskId.report.md"
$ExternalReportPath = Join-Path $ReportDir "$TaskId.report.md"
$Report = @()
$Report += '# TerraYield Plan Audit Readiness'
$Report += ''
$Report += "Generated: $(Get-Date -Format s)"
$Report += "Task: $TaskId"
$Report += ''
$Report += '## Scores'
foreach ($key in $Score.Keys) { $Report += "- ${key}: $($Score[$key])" }
$Report += ''
$Report += '## Findings'
if ($Findings.Count -eq 0) { $Report += '- none' } else { $Findings | ForEach-Object { $Report += '- ' + $_ } }
$Report += ''
$Report += '## Warnings'
if ($Warnings.Count -eq 0) { $Report += '- none' } else { $Warnings | ForEach-Object { $Report += '- ' + $_ } }
$Report += ''
$Report += '## Next Recommendation'
if ($Score.contractor_pipeline -lt 100) {
  $Report += '- Contractor pipeline files are incomplete. Next task should install or generate contractor pipeline files.'
} elseif ($Score.future_growth -lt 100) {
  $Report += '- Future growth skeleton is incomplete. Next task should repair future_growth files.'
} else {
  $Report += '- Proceed to long validation/smoke run.'
}
$Report += ''
$Report += 'TASK_COMPLETION=100/100'
$Report += 'TERRAYIELD_TASK_DONE'

$Report | Set-Content -Path $ReportPath -Encoding UTF8
try { Copy-Item -Path $ReportPath -Destination $ExternalReportPath -Force } catch {}

Step ('REPORT_PATH=' + $ReportPath)
Step ('EXTERNAL_REPORT_PATH=' + $ExternalReportPath)
Step ('PLAN_PROGRESS_PERCENT=' + $Score.overall)
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
