[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = if ($env:AAYS_REPO_ROOT) {
  [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
}

$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
& $git.Source -C $repoRoot rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { throw "AAYS_REPO_ROOT_NOT_GIT_WORKTREE: $repoRoot" }

# The Python worker must use the same checkout as the PowerShell carrier.
$env:AAYS_REPO_ROOT = $repoRoot
$env:PYTHONUTF8 = '1'

$pythonRepoPath = 'docs/chatgpt_status/parcel_label/automation/parcel_label_3_exact_points_and_historical_audit_v1.py'
$pythonScript = Join-Path $repoRoot ($pythonRepoPath -replace '/', '\')
$tempScript = $null

if (-not (Test-Path -LiteralPath $pythonScript -PathType Leaf)) {
  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_parcel_label_slot3'
  New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
  $tempScript = Join-Path $tempRoot 'parcel_label_3_exact_points_and_historical_audit_v1.py'
  $resolved = $false
  foreach ($ref in @('HEAD','origin/main','main','origin/codex/aays-single-runner-v5-20260706','codex/aays-single-runner-v5-20260706')) {
    & $git.Source -C $repoRoot show "$ref`:$pythonRepoPath" 2>$null | Set-Content -LiteralPath $tempScript -Encoding UTF8
    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $tempScript -PathType Leaf) -and ((Get-Item -LiteralPath $tempScript).Length -gt 0)) {
      $pythonScript = $tempScript
      $resolved = $true
      break
    }
  }
  if (-not $resolved) { throw "PARCEL_LABEL_3_PYTHON_SCRIPT_MISSING: $pythonRepoPath" }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

$runnerOutput = Join-Path $repoRoot 'docs\chatgpt_status\parcel_label\runner_outputs\parcel_label_3_exact_points_and_historical_audit_latest.json'
$websiteOutput = Join-Path $repoRoot 'england_map_web\data\distance_property_types\parcel_label_3_canonical_probe_latest.json'

Write-Output 'SLOT_ID=parcel_label_3'
Write-Output 'TASK_VERSION=1.2-path-safe-fail-closed-carrier'
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "AAYS_REPO_ROOT_EFFECTIVE=$env:AAYS_REPO_ROOT"
Write-Output "PYTHON_SCRIPT=$pythonScript"
Write-Output 'SECURITY_SCORE_FIELDS_ALLOWED=false'

if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
  & $python.Source -3 $pythonScript
} else {
  & $python.Source $pythonScript
}
$pythonExitCode = $LASTEXITCODE
if ($null -eq $pythonExitCode) { $pythonExitCode = 1 }

$runnerOutputPresent = Test-Path -LiteralPath $runnerOutput -PathType Leaf
$websiteOutputPresent = Test-Path -LiteralPath $websiteOutput -PathType Leaf
$outputsPresent = $runnerOutputPresent -and $websiteOutputPresent

# Exit 2 means the Python worker produced a valid fail-closed report. Let the
# shared runner commit those reports instead of treating the task as crashed.
if (($pythonExitCode -eq 0 -or $pythonExitCode -eq 2) -and $outputsPresent) {
  $carrierExitCode = 0
} elseif ($pythonExitCode -eq 0 -and -not $outputsPresent) {
  $carrierExitCode = 3
} else {
  $carrierExitCode = $pythonExitCode
}

Write-Output "PYTHON_EXIT_CODE=$pythonExitCode"
Write-Output "RUNNER_OUTPUT_PRESENT=$($runnerOutputPresent.ToString().ToLowerInvariant())"
Write-Output "WEBSITE_OUTPUT_PRESENT=$($websiteOutputPresent.ToString().ToLowerInvariant())"
Write-Output "CARRIER_EXIT_CODE=$carrierExitCode"
Write-Output 'FINAL_READY=false'
exit $carrierExitCode
