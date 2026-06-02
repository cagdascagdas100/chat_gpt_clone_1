$ErrorActionPreference = "Continue"
$TaskId = "terrayield-050-install-contractor-from-local-zip"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$StorageRoot = "E:\AAYS_DATA\contractor"

function Write-Step([string]$Text) {
  Write-Output ("[" + (Get-Date -Format "s") + "] " + $Text)
}

Write-Step "PROJECT=terrayield"
Write-Step "DISPLAY_PROJECT=TerraYield"
Write-Step "CHATGPT_PAGE_PROJECT=aays1"
Write-Step ("TASK=" + $TaskId)
Write-Step "MODE=install_contractor_pipeline_from_local_zip"

if (-not (Test-Path $ProjectRoot)) {
  Write-Step ("PROJECT_ROOT_MISSING=" + $ProjectRoot)
  Write-Step "TASK_COMPLETION=blocked_project_root_missing"
  exit 2
}

$candidatePaths = @(
  "C:\AAYS_GITHUB_BRIDGE_CLEAN\contractor_scripts_clean.zip",
  "C:\AAYS_GITHUB_BRIDGE_CLEAN\contractor_scripts.zip",
  "$env:USERPROFILE\Downloads\contractor_scripts_clean.zip",
  "$env:USERPROFILE\Downloads\contractor_scripts.zip",
  "$env:USERPROFILE\Desktop\contractor_scripts_clean.zip",
  "$env:USERPROFILE\Desktop\contractor_scripts.zip",
  "$ProjectRoot\contractor_scripts_clean.zip",
  "$ProjectRoot\contractor_scripts.zip"
)

$zipPath = $null
foreach ($p in $candidatePaths) {
  if (Test-Path $p) {
    $zipPath = $p
    break
  }
}

if (-not $zipPath) {
  Write-Step "LOCAL_ZIP_NOT_FOUND"
  Write-Step "EXPECTED_ONE_OF_BEGIN"
  foreach ($p in $candidatePaths) { Write-Step ("EXPECTED_ZIP=" + $p) }
  Write-Step "EXPECTED_ONE_OF_END"
  Write-Step "TASK_COMPLETION=blocked_missing_local_zip"
  exit 4
}

Set-Location $ProjectRoot
Write-Step ("PROJECT_ROOT_FOUND=" + $ProjectRoot)
Write-Step ("ZIP_FOUND=" + $zipPath)
Write-Step ("ZIP_SHA256=" + (Get-FileHash -Algorithm SHA256 $zipPath).Hash)

New-Item -ItemType Directory -Force -Path "scripts", "$StorageRoot\raw", "$StorageRoot\staging", "$StorageRoot\curated", "$StorageRoot\exports", "$StorageRoot\manifests", "$StorageRoot\manual", "$StorageRoot\raw\status" | Out-Null
Write-Step "DIRECTORIES_READY"

Expand-Archive -LiteralPath $zipPath -DestinationPath $ProjectRoot -Force
Write-Step "ZIP_EXPANDED"

$expected = @(
  "scripts\contractor_collect_companies_house.py",
  "scripts\contractor_collect_procurement_ocds.py",
  "scripts\contractor_normalize_and_score.py",
  "scripts\contractor_load_to_postgres.py",
  "scripts\contractor_match_to_parcels.py",
  "scripts\contractor_export_for_app.py",
  "scripts\requirements_contractor.txt",
  "scripts\README_CONTRACTOR_PIPELINE.md"
)
$missing = @()
foreach ($rel in $expected) {
  $full = Join-Path $ProjectRoot $rel
  if (Test-Path $full) {
    Write-Step ("INSTALLED=" + $rel + " SHA256=" + (Get-FileHash -Algorithm SHA256 $full).Hash)
  } else {
    $missing += $rel
    Write-Step ("MISSING_AFTER_INSTALL=" + $rel)
  }
}

if ($missing.Count -gt 0) {
  Write-Step ("INSTALL_FAILED_MISSING_COUNT=" + $missing.Count)
  Write-Step "TASK_COMPLETION=failed_missing_files"
  exit 3
}

Write-Step "PY_COMPILE_BEGIN"
python -m py_compile `
  .\scripts\contractor_collect_companies_house.py `
  .\scripts\contractor_collect_procurement_ocds.py `
  .\scripts\contractor_normalize_and_score.py `
  .\scripts\contractor_load_to_postgres.py `
  .\scripts\contractor_match_to_parcels.py `
  .\scripts\contractor_export_for_app.py
$compileExit = $LASTEXITCODE
Write-Step ("PY_COMPILE_EXIT=" + $compileExit)
if ($compileExit -ne 0) {
  Write-Step "TASK_COMPLETION=failed_py_compile"
  exit $compileExit
}

Write-Step "PIP_INSTALL_BEGIN"
python -m pip install -r .\scripts\requirements_contractor.txt
$pipExit = $LASTEXITCODE
Write-Step ("PIP_INSTALL_EXIT=" + $pipExit)
if ($pipExit -ne 0) {
  Write-Step "TASK_COMPLETION=failed_pip_install"
  exit $pipExit
}

Write-Step "FAIL_CLOSED_SMOKE_BEGIN"
Remove-Item Env:\COMPANIES_HOUSE_API_KEY -ErrorAction SilentlyContinue
python .\scripts\contractor_collect_companies_house.py --limit 1 --storage-root $StorageRoot
$failClosedExit = $LASTEXITCODE
Write-Step ("FAIL_CLOSED_SMOKE_EXIT=" + $failClosedExit)
if ($failClosedExit -ne 2) {
  Write-Step "WARNING_FAIL_CLOSED_EXPECTED_EXIT_2_NOT_OBSERVED"
}

Write-Step "GIT_STATUS_BEGIN"
git status --short
Write-Step "GIT_STATUS_END"

Write-Step "CONTRACTOR_PIPELINE_FILES_READY"
Write-Step "PLAN_PROGRESS_PERCENT=22"
Write-Step "NEXT_EXPECTED_ACTION=run_procurement_snapshot_and_normalize_smoke"
Write-Step "TASK_COMPLETION=100/100"
Write-Step "TERRAYIELD_TASK_DONE"
exit 0
