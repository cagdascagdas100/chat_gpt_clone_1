$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
$ReportDir = Join-Path $Repo "docs\chatgpt_handoff\cloud_ready_20260517"
$ReportPath = Join-Path $ReportDir "016_CLEAN_FULL_PYTEST_REPORT.txt"
$RawPath = Join-Path $ReportDir "016_CLEAN_FULL_PYTEST_RAW.txt"
$TaskName = "016_CLEAN_FULL_PYTEST_RERUN"
$ExpectedBranch = "security-accuracy-expansion-20260508"

function Write-KvReportLine {
  param(
    [Parameter(Mandatory=$true)][string]$Key,
    [Parameter(Mandatory=$true)][AllowEmptyString()][string]$Value
  )
  Add-Content -LiteralPath $ReportPath -Value ($Key + "=" + $Value) -Encoding UTF8
}

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
if (Test-Path -LiteralPath $ReportPath) { Remove-Item -LiteralPath $ReportPath -Force }
if (Test-Path -LiteralPath $RawPath) { Remove-Item -LiteralPath $RawPath -Force }

$StartUtc = (Get-Date).ToUniversalTime()
$Branch = "unknown"
$Head = "unknown"
$PytestExitCode = 999
$PytestStatus = "failed"
$CollectionGuardStatus = "unknown"
$Blockers = "none"
$DurationSeconds = 0

try {
  if (-not (Test-Path -LiteralPath $Repo)) {
    throw "Repo path not found: $Repo"
  }
  Set-Location -LiteralPath $Repo

  $Branch = (git branch --show-current).Trim()
  $Head = (git rev-parse --short HEAD).Trim()

  $PytestIniPath = Join-Path $Repo "pytest.ini"
  if (-not (Test-Path -LiteralPath $PytestIniPath)) {
    throw "pytest.ini not found"
  }

  $PytestIni = Get-Content -LiteralPath $PytestIniPath -Raw
  if ($PytestIni -match "testpaths\s*=\s*tests" -and $PytestIni -match "norecursedirs" -and $PytestIni -match "docs/chatgpt_handoff") {
    $CollectionGuardStatus = "passed"
  } else {
    $CollectionGuardStatus = "failed"
  }

  "# 016 clean full pytest raw output" | Set-Content -LiteralPath $RawPath -Encoding UTF8
  "timestamp_utc=$($StartUtc.ToString("o"))" | Add-Content -LiteralPath $RawPath -Encoding UTF8
  "branch=$Branch" | Add-Content -LiteralPath $RawPath -Encoding UTF8
  "head=$Head" | Add-Content -LiteralPath $RawPath -Encoding UTF8
  "command=python -m pytest -q" | Add-Content -LiteralPath $RawPath -Encoding UTF8
  "" | Add-Content -LiteralPath $RawPath -Encoding UTF8

  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = "python"
  $psi.Arguments = "-m pytest -q"
  $psi.WorkingDirectory = $Repo
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $psi.CreateNoWindow = $true

  $process = New-Object System.Diagnostics.Process
  $process.StartInfo = $psi
  [void]$process.Start()
  $stdout = $process.StandardOutput.ReadToEnd()
  $stderr = $process.StandardError.ReadToEnd()
  $process.WaitForExit()
  $PytestExitCode = $process.ExitCode

  "## STDOUT" | Add-Content -LiteralPath $RawPath -Encoding UTF8
  $stdout | Add-Content -LiteralPath $RawPath -Encoding UTF8
  "" | Add-Content -LiteralPath $RawPath -Encoding UTF8
  "## STDERR" | Add-Content -LiteralPath $RawPath -Encoding UTF8
  $stderr | Add-Content -LiteralPath $RawPath -Encoding UTF8

  if ($PytestExitCode -eq 0) {
    $PytestStatus = "passed"
  } else {
    $PytestStatus = "failed"
    $Blockers = "clean_full_pytest_failed"
  }

  if ($CollectionGuardStatus -ne "passed") {
    $Blockers = if ($Blockers -eq "none") { "pytest_collection_guard_failed" } else { $Blockers + ";pytest_collection_guard_failed" }
  }
} catch {
  $PytestStatus = "failed"
  $Blockers = "runner_exception"
  "RUNNER_EXCEPTION=$($_.Exception.Message)" | Set-Content -LiteralPath $RawPath -Encoding UTF8
} finally {
  $EndUtc = (Get-Date).ToUniversalTime()
  $DurationSeconds = [Math]::Round(($EndUtc - $StartUtc).TotalSeconds, 2)

  Write-KvReportLine "timestamp_utc" $EndUtc.ToString("o")
  Write-KvReportLine "task" $TaskName
  Write-KvReportLine "report_type" "actual_clean_full_pytest_output"
  Write-KvReportLine "checked_branch" $ExpectedBranch
  Write-KvReportLine "actual_branch" $Branch
  Write-KvReportLine "head" $Head
  Write-KvReportLine "pytest_ini_present" ([string](Test-Path -LiteralPath (Join-Path $Repo "pytest.ini"))).ToLowerInvariant()
  Write-KvReportLine "pytest_collection_guard_status" $CollectionGuardStatus
  Write-KvReportLine "full_pytest_status" $PytestStatus
  Write-KvReportLine "pytest_exit_code" ([string]$PytestExitCode)
  Write-KvReportLine "raw_output" $RawPath
  Write-KvReportLine "duration_seconds" ([string]$DurationSeconds)
  Write-KvReportLine "public_url_verified" "false"
  Write-KvReportLine "cloud_db_verified" "false"
  Write-KvReportLine "classification_recommendation" "CLOUD_READY_PENDING_PROVIDER"
  Write-KvReportLine "next_single_action" "WAIT_FOR_USER_PROVIDER_DECISION"
  Write-KvReportLine "blockers" $Blockers
  Write-KvReportLine "secret_values_printed" "false"
  Write-KvReportLine "db_write" "none"
  Write-KvReportLine "ddl" "none"
  Write-KvReportLine "migration_apply" "none"
  Write-KvReportLine "prod_deploy" "none"

  git add -- docs/chatgpt_handoff/cloud_ready_20260517/016_CLEAN_FULL_PYTEST_REPORT.txt docs/chatgpt_handoff/cloud_ready_20260517/016_CLEAN_FULL_PYTEST_RAW.txt | Out-Null
  $gitDiff = git diff --cached --name-only
  if ($gitDiff) {
    git commit -m "Publish 016 clean full pytest evidence" | Out-Null
    git push | Out-Null
  }
}

if ($PytestStatus -eq "passed" -and $CollectionGuardStatus -eq "passed") {
  exit 0
}
exit 1
