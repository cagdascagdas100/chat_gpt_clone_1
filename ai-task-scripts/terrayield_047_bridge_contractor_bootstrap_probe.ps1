$ErrorActionPreference = "Continue"
$TaskId = "terrayield-047-bridge-contractor-bootstrap-probe"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$StorageRoot = "E:\AAYS_DATA\contractor"

function Write-Step([string]$Text) {
  Write-Output ("[" + (Get-Date -Format "s") + "] " + $Text)
}

Write-Step "PROJECT=terrayield"
Write-Step "DISPLAY_PROJECT=TerraYield"
Write-Step "CHATGPT_PAGE_PROJECT=aays1"
Write-Step ("TASK=" + $TaskId)
Write-Step "MODE=bridge_bootstrap_probe"
Write-Step ("COMPUTER=" + $env:COMPUTERNAME)
Write-Step ("USER=" + $env:USERNAME)
Write-Step ("PWD_INITIAL=" + (Get-Location).Path)
Write-Step ("POWERSHELL_VERSION=" + $PSVersionTable.PSVersion.ToString())

if (-not (Test-Path $ProjectRoot)) {
  Write-Step ("PROJECT_ROOT_MISSING=" + $ProjectRoot)
  Write-Step "TASK_COMPLETION=blocked_project_root_missing"
  exit 2
}

Set-Location $ProjectRoot
Write-Step ("PROJECT_ROOT_FOUND=" + $ProjectRoot)
Write-Step ("PWD_PROJECT=" + (Get-Location).Path)

New-Item -ItemType Directory -Force -Path `
  "$StorageRoot\raw", "$StorageRoot\staging", "$StorageRoot\curated", "$StorageRoot\exports", "$StorageRoot\manifests", "$StorageRoot\manual", "$StorageRoot\raw\status" | Out-Null
Write-Step ("STORAGE_ROOT_READY=" + $StorageRoot)

Write-Step "PYTHON_CHECK_BEGIN"
python --version 2>&1 | Out-String | Write-Output
Write-Step "PYTHON_CHECK_END"

Write-Step "GIT_STATUS_BEGIN"
git status --short 2>&1 | Out-String | Write-Output
Write-Step "GIT_STATUS_END"

Write-Step "CONTRACTOR_FILE_CHECK_BEGIN"
$files = @(
  "scripts\contractor_collect_companies_house.py",
  "scripts\contractor_collect_procurement_ocds.py",
  "scripts\contractor_normalize_and_score.py",
  "scripts\contractor_load_to_postgres.py",
  "scripts\contractor_match_to_parcels.py",
  "scripts\contractor_export_for_app.py",
  "scripts\requirements_contractor.txt",
  "scripts\README_CONTRACTOR_PIPELINE.md"
)
$present = 0
$missing = 0
foreach ($rel in $files) {
  if (Test-Path (Join-Path $ProjectRoot $rel)) {
    Write-Step ("FOUND=" + $rel)
    $present++
  } else {
    Write-Step ("MISSING=" + $rel)
    $missing++
  }
}
Write-Step ("CONTRACTOR_FILES_PRESENT=" + $present)
Write-Step ("CONTRACTOR_FILES_MISSING=" + $missing)
Write-Step "CONTRACTOR_FILE_CHECK_END"

Write-Step "RUNNER_BRIDGE_PROBE_OK"
Write-Step "NEXT_EXPECTED_ACTION=install_or_refresh_contractor_pipeline_files"
Write-Step "TASK_COMPLETION=100/100"
Write-Step "TERRAYIELD_TASK_DONE"
exit 0
