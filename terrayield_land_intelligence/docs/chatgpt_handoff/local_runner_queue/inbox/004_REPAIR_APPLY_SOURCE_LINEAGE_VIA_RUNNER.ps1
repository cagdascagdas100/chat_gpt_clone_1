$ErrorActionPreference = "Stop"

$TaskName = "004_REPAIR_APPLY_SOURCE_LINEAGE_VIA_RUNNER"
$ExpectedBranch = "security-accuracy-expansion-20260508"
$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
$MainRepo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$EvidenceDir = Join-Path $Repo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
$MainEvidenceDir = Join-Path $MainRepo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
$AutomationScript = Join-Path $Repo "docs\chatgpt_handoff\github_visible_source_lineage_20260516\REPAIR_APPLY_SOURCE_LINEAGE_APPLICATION.ps1"

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
New-Item -ItemType Directory -Force -Path $MainEvidenceDir | Out-Null

$Report = Join-Path $EvidenceDir "004_RUNNER_REPAIR_APPLY_REPORT.txt"
$Blockers = Join-Path $EvidenceDir "004_RUNNER_REPAIR_APPLY_BLOCKERS.md"
$Stdout = Join-Path $EvidenceDir "004_RUNNER_REPAIR_APPLY_STDOUT.txt"
$RunnerStatus = Join-Path $EvidenceDir "004_RUNNER_REPAIR_APPLY_STATUS.txt"
$BlockerList = New-Object System.Collections.Generic.List[string]

function Add-Blocker([string]$Name) {
  if (-not $BlockerList.Contains($Name)) { $BlockerList.Add($Name) }
}

Set-Location $Repo
$Branch = (git branch --show-current).Trim()
$HeadBefore = (git rev-parse --short=12 HEAD).Trim()

if ($Branch -ne $ExpectedBranch) {
  Add-Blocker "BRANCH_MISMATCH:$Branch"
}

# Always pull first so the latest automation script and snapshot are present.
$PullOutput = git pull origin $ExpectedBranch 2>&1
$PullExit = $LASTEXITCODE
if ($PullExit -ne 0) {
  Add-Blocker "GIT_PULL_FAILED"
}

if (!(Test-Path $AutomationScript)) {
  Add-Blocker "AUTOMATION_SCRIPT_NOT_FOUND"
}

$AutomationExit = $null
if ($BlockerList.Count -eq 0) {
  $AutomationOutput = powershell -ExecutionPolicy Bypass -File $AutomationScript 2>&1
  $AutomationExit = $LASTEXITCODE
  $AutomationOutput | Set-Content -LiteralPath $Stdout -Encoding UTF8
  if ($AutomationExit -ne 0) {
    Add-Blocker "AUTOMATION_SCRIPT_FAILED"
  }
} else {
  @("automation_not_run_due_to_blockers") | Set-Content -LiteralPath $Stdout -Encoding UTF8
}

$RepairReport = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_REPORT.txt"
$RepairBlockers = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_BLOCKERS.md"
$RepairPytest = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_PYTEST.txt"
$RepairImportProbe = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_IMPORT_PROBE.txt"

$FinalFromRepair = "unknown"
$NextFromRepair = "unknown"
$PytestExitFromRepair = "unknown"
$CommitStatusFromRepair = "unknown"
$PushStatusFromRepair = "unknown"
$CommitHashFromRepair = ""

if (Test-Path $RepairReport) {
  $rr = Get-Content $RepairReport
  foreach ($line in $rr) {
    if ($line -like "final_classification=*") { $FinalFromRepair = $line.Substring("final_classification=".Length) }
    if ($line -like "next_single_action=*") { $NextFromRepair = $line.Substring("next_single_action=".Length) }
    if ($line -like "pytest_exit_code=*") { $PytestExitFromRepair = $line.Substring("pytest_exit_code=".Length) }
    if ($line -like "commit_status=*") { $CommitStatusFromRepair = $line.Substring("commit_status=".Length) }
    if ($line -like "push_status=*") { $PushStatusFromRepair = $line.Substring("push_status=".Length) }
    if ($line -like "commit_hash=*") { $CommitHashFromRepair = $line.Substring("commit_hash=".Length) }
  }
}

$HeadAfter = (git rev-parse --short=12 HEAD).Trim()
$Final = if ($BlockerList.Count -eq 0 -and $FinalFromRepair -eq "SOURCE_LINEAGE_APPLICATION_REPAIR_READY") { "RUNNER_REPAIR_APPLY_READY" } else { "BLOCKED" }
if ($Final -eq "BLOCKED" -and $BlockerList.Count -eq 0) { Add-Blocker "REPAIR_NOT_READY:$FinalFromRepair" }
$Next = if ($Final -eq "RUNNER_REPAIR_APPLY_READY") { "run_api_smoke_and_sync_main_repo" } else { $BlockerList[0] }

@(
  "timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
  "task=$TaskName",
  "repo=$Repo",
  "main_repo=$MainRepo",
  "branch=$Branch",
  "head_before=$HeadBefore",
  "head_after=$HeadAfter",
  "git_pull_exit_code=$PullExit",
  "automation_script=$AutomationScript",
  "automation_exit_code=$AutomationExit",
  "automation_stdout=$Stdout",
  "repair_report=$RepairReport",
  "repair_blockers=$RepairBlockers",
  "repair_pytest=$RepairPytest",
  "repair_import_probe=$RepairImportProbe",
  "repair_final_classification=$FinalFromRepair",
  "repair_next_single_action=$NextFromRepair",
  "repair_pytest_exit_code=$PytestExitFromRepair",
  "repair_commit_status=$CommitStatusFromRepair",
  "repair_push_status=$PushStatusFromRepair",
  "repair_commit_hash=$CommitHashFromRepair",
  "db_write=none",
  "ddl=none",
  "migration_apply=none",
  "prod_deploy=none",
  "secret_values_printed=false",
  "final_classification=$Final",
  "next_single_action=$Next"
) | Set-Content -LiteralPath $Report -Encoding UTF8

$BlockerLines = @("# 004 Runner Repair Apply Blockers", "")
if ($BlockerList.Count -eq 0) {
  $BlockerLines += "- none"
} else {
  foreach ($b in $BlockerList) { $BlockerLines += "- $b" }
}
$BlockerLines | Set-Content -LiteralPath $Blockers -Encoding UTF8

@(
  "task=$TaskName",
  "final_classification=$Final",
  "next_single_action=$Next",
  "report=$Report",
  "blockers=$Blockers"
) | Set-Content -LiteralPath $RunnerStatus -Encoding UTF8

Copy-Item -LiteralPath $Report -Destination (Join-Path $MainEvidenceDir "004_RUNNER_REPAIR_APPLY_REPORT.txt") -Force
Copy-Item -LiteralPath $Blockers -Destination (Join-Path $MainEvidenceDir "004_RUNNER_REPAIR_APPLY_BLOCKERS.md") -Force
Copy-Item -LiteralPath $Stdout -Destination (Join-Path $MainEvidenceDir "004_RUNNER_REPAIR_APPLY_STDOUT.txt") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $RunnerStatus -Destination (Join-Path $MainEvidenceDir "004_RUNNER_REPAIR_APPLY_STATUS.txt") -Force

Get-Content $Report
Write-Host ""
Get-Content $Blockers
