[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = if ($env:AAYS_REPO_ROOT) {
  [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
}

$pythonRepoPath = 'docs/chatgpt_status/height_difference/automation/height_difference_1_official_boundary_and_wcs_v1.py'
$pythonScript = Join-Path $repoRoot ($pythonRepoPath -replace '/', '\')
$tempScript = $null

if (-not (Test-Path -LiteralPath $pythonScript -PathType Leaf)) {
  $git = Get-Command git -ErrorAction SilentlyContinue
  if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND_FOR_PYTHON_FALLBACK' }
  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1'
  New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
  $tempScript = Join-Path $tempRoot 'height_difference_1_official_boundary_and_wcs_v1.py'
  $resolved = $false
  foreach ($ref in @('origin/agent/height-difference-1-executable-evidence-r3-20260722','origin/main','main')) {
    & $git.Source -C $repoRoot show "$ref`:$pythonRepoPath" 2>$null | Set-Content -LiteralPath $tempScript -Encoding UTF8
    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $tempScript -PathType Leaf) -and ((Get-Item -LiteralPath $tempScript).Length -gt 0)) {
      $pythonScript = $tempScript
      $resolved = $true
      break
    }
  }
  if (-not $resolved) { throw "HEIGHT_DIFFERENCE_1_PYTHON_SCRIPT_MISSING: $pythonRepoPath" }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

$runnerOutput = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\shards\height_difference_1\runner_outputs\official_boundary_and_wcs_latest.json'
$websiteOutput = Join-Path $repoRoot 'england_map_web\data\aays_18_slots\height_difference_1\verified_results_latest.json'

Write-Output 'SLOT_ID=height_difference_1'
Write-Output 'TASK_VERSION=1.1-hardened-fail-closed'
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "PYTHON_SCRIPT=$pythonScript"
Write-Output 'SINGLE_SHARED_RUNNER_ONLY=true'
Write-Output 'NEW_RUNNER_ALLOWED=false'
Write-Output 'RUNNER_EXECUTION_CLAIMED=true'
Write-Output 'DB_WRITE=false'
Write-Output 'MIGRATION=false'
Write-Output 'PRODUCTION_DEPLOY=false'

if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
  & $python.Source -3 $pythonScript --self-test
} else {
  & $python.Source $pythonScript --self-test
}
$selfTestExitCode = $LASTEXITCODE
if ($null -eq $selfTestExitCode) { $selfTestExitCode = 1 }
Write-Output "SELF_TEST_EXIT_CODE=$selfTestExitCode"
if ($selfTestExitCode -ne 0) {
  Write-Output 'FINAL_READY=false'
  exit $selfTestExitCode
}

$arguments = @(
  $pythonScript,
  '--repo-root', $repoRoot,
  '--runner-output', $runnerOutput,
  '--website-output', $websiteOutput,
  '--max-workers', '4'
)
if ($env:HMLR_BARKING_DAGENHAM_GML_URL) {
  $arguments += @('--hmlr-gml-url', $env:HMLR_BARKING_DAGENHAM_GML_URL)
}
if ($env:HEIGHT_DIFFERENCE_1_SURVEY_METADATA_JSON) {
  $arguments += @('--survey-metadata-json', $env:HEIGHT_DIFFERENCE_1_SURVEY_METADATA_JSON)
}

if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
  & $python.Source -3 @arguments
} else {
  & $python.Source @arguments
}
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 1 }
Write-Output "PYTHON_EXIT_CODE=$exitCode"
Write-Output 'FINAL_READY=false'
exit $exitCode
