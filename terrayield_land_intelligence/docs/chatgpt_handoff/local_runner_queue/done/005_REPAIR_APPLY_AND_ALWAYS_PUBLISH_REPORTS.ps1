$ErrorActionPreference = "Continue"

$TaskName = "005_REPAIR_APPLY_AND_ALWAYS_PUBLISH_REPORTS"
$ExpectedBranch = "security-accuracy-expansion-20260508"
$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
$MainRepo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$EvidenceDir = Join-Path $Repo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
$MainEvidenceDir = Join-Path $MainRepo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
$AutomationScript = Join-Path $Repo "docs\chatgpt_handoff\github_visible_source_lineage_20260516\REPAIR_APPLY_SOURCE_LINEAGE_APPLICATION.ps1"

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
New-Item -ItemType Directory -Force -Path $MainEvidenceDir | Out-Null

$Report = Join-Path $EvidenceDir "005_RUNNER_REPAIR_ALWAYS_PUBLISH_REPORT.txt"
$Blockers = Join-Path $EvidenceDir "005_RUNNER_REPAIR_ALWAYS_PUBLISH_BLOCKERS.md"
$Stdout = Join-Path $EvidenceDir "005_RUNNER_REPAIR_ALWAYS_PUBLISH_STDOUT.txt"
$PublishLog = Join-Path $EvidenceDir "005_RUNNER_REPAIR_ALWAYS_PUBLISH_GIT_LOG.txt"
$BlockerList = New-Object System.Collections.Generic.List[string]

function Add-Blocker([string]$Name) {
  if (-not $BlockerList.Contains($Name)) { $BlockerList.Add($Name) }
}

Set-Location $Repo
$Branch = (git branch --show-current).Trim()
$HeadBefore = (git rev-parse --short=12 HEAD).Trim()

if ($Branch -ne $ExpectedBranch) { Add-Blocker "BRANCH_MISMATCH:$Branch" }

$PullOutput = git pull origin $ExpectedBranch 2>&1
$PullExit = $LASTEXITCODE
if ($PullExit -ne 0) { Add-Blocker "GIT_PULL_FAILED" }

if (!(Test-Path $AutomationScript)) { Add-Blocker "AUTOMATION_SCRIPT_NOT_FOUND" }

$AutomationExit = $null
if ($BlockerList.Count -eq 0) {
  $AutomationOutput = powershell -ExecutionPolicy Bypass -File $AutomationScript 2>&1
  $AutomationExit = $LASTEXITCODE
  $AutomationOutput | Set-Content -LiteralPath $Stdout -Encoding UTF8
} else {
  @("automation_not_run_due_to_pre_blockers") | Set-Content -LiteralPath $Stdout -Encoding UTF8
}

$RepairReport = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_REPORT.txt"
$RepairBlockers = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_BLOCKERS.md"
$RepairPytest = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_PYTEST.txt"
$RepairImportProbe = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_IMPORT_PROBE.txt"
$RepairDiffCheck = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_DIFF_CHECK.txt"
$RepairPublishLog = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_PUBLISH_LOG.txt"

$RepairFinal = "unknown"
$RepairNext = "unknown"
$RepairPatchExit = "unknown"
$RepairDiffExit = "unknown"
$RepairPytestExit = "unknown"
$RepairCommitStatus = "unknown"
$RepairPushStatus = "unknown"
$RepairCommitHash = ""

if (Test-Path $RepairReport) {
  foreach ($line in (Get-Content $RepairReport)) {
    if ($line -like "final_classification=*") { $RepairFinal = $line.Substring("final_classification=".Length) }
    if ($line -like "next_single_action=*") { $RepairNext = $line.Substring("next_single_action=".Length) }
    if ($line -like "patch_exit_code=*") { $RepairPatchExit = $line.Substring("patch_exit_code=".Length) }
    if ($line -like "diff_check_exit_code=*") { $RepairDiffExit = $line.Substring("diff_check_exit_code=".Length) }
    if ($line -like "pytest_exit_code=*") { $RepairPytestExit = $line.Substring("pytest_exit_code=".Length) }
    if ($line -like "commit_status=*") { $RepairCommitStatus = $line.Substring("commit_status=".Length) }
    if ($line -like "push_status=*") { $RepairPushStatus = $line.Substring("push_status=".Length) }
    if ($line -like "commit_hash=*") { $RepairCommitHash = $line.Substring("commit_hash=".Length) }
  }
} else {
  Add-Blocker "REPAIR_REPORT_MISSING"
}

$Final = if ($BlockerList.Count -eq 0 -and $RepairFinal -eq "SOURCE_LINEAGE_APPLICATION_REPAIR_READY") { "RUNNER_REPAIR_ALWAYS_PUBLISH_READY" } else { "BLOCKED" }
if ($Final -eq "BLOCKED" -and $BlockerList.Count -eq 0) { Add-Blocker "REPAIR_NOT_READY:$RepairFinal" }
$Next = if ($Final -eq "RUNNER_REPAIR_ALWAYS_PUBLISH_READY") { "chatgpt_review_github_reports_then_queue_api_smoke" } else { $BlockerList[0] }
$HeadAfter = (git rev-parse --short=12 HEAD).Trim()

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
  "repair_diff_check=$RepairDiffCheck",
  "repair_publish_log=$RepairPublishLog",
  "repair_final_classification=$RepairFinal",
  "repair_next_single_action=$RepairNext",
  "repair_patch_exit_code=$RepairPatchExit",
  "repair_diff_check_exit_code=$RepairDiffExit",
  "repair_pytest_exit_code=$RepairPytestExit",
  "repair_commit_status=$RepairCommitStatus",
  "repair_push_status=$RepairPushStatus",
  "repair_commit_hash=$RepairCommitHash",
  "db_write=none",
  "ddl=none",
  "migration_apply=none",
  "prod_deploy=none",
  "secret_values_printed=false",
  "final_classification=$Final",
  "next_single_action=$Next"
) | Set-Content -LiteralPath $Report -Encoding UTF8

$BlockerLines = @("# 005 Runner Repair Always Publish Blockers", "")
if ($BlockerList.Count -eq 0) { $BlockerLines += "- none" } else { foreach ($b in $BlockerList) { $BlockerLines += "- $b" } }
$BlockerLines | Set-Content -LiteralPath $Blockers -Encoding UTF8

Copy-Item -LiteralPath $Report -Destination (Join-Path $MainEvidenceDir "005_RUNNER_REPAIR_ALWAYS_PUBLISH_REPORT.txt") -Force
Copy-Item -LiteralPath $Blockers -Destination (Join-Path $MainEvidenceDir "005_RUNNER_REPAIR_ALWAYS_PUBLISH_BLOCKERS.md") -Force
Copy-Item -LiteralPath $Stdout -Destination (Join-Path $MainEvidenceDir "005_RUNNER_REPAIR_ALWAYS_PUBLISH_STDOUT.txt") -Force -ErrorAction SilentlyContinue

# Always publish reports to GitHub so ChatGPT can read them without manual upload.
git add "docs/chatgpt_handoff/parcel_location_evidence_wave_20260516" `
  "docs/chatgpt_handoff/local_runner_queue/done" `
  "docs/chatgpt_handoff/local_runner_queue/failed" `
  "docs/chatgpt_handoff/local_runner_queue/outputs" 2>&1 | Tee-Object -FilePath $PublishLog

$Cached = git diff --cached --name-only
$ReportCommitStatus = "not_attempted"
$ReportPushStatus = "not_attempted"
$ReportCommitHash = ""
if ($Cached) {
  git commit -m "Publish local runner repair reports" 2>&1 | Tee-Object -FilePath $PublishLog -Append
  if ($LASTEXITCODE -eq 0) {
    $ReportCommitStatus = "committed"
    $ReportCommitHash = (git rev-parse --short=12 HEAD).Trim()
    git push origin $Branch 2>&1 | Tee-Object -FilePath $PublishLog -Append
    if ($LASTEXITCODE -eq 0) { $ReportPushStatus = "pushed" } else { $ReportPushStatus = "push_failed" }
  } else {
    $ReportCommitStatus = "commit_failed"
  }
} else {
  $ReportCommitStatus = "nothing_to_commit"
}

Add-Content -LiteralPath $Report -Encoding UTF8 -Value @(
  "report_commit_status=$ReportCommitStatus",
  "report_commit_hash=$ReportCommitHash",
  "report_push_status=$ReportPushStatus",
  "final_report_written_after_publish=true"
)

Get-Content $Report
Write-Host ""
Get-Content $Blockers
