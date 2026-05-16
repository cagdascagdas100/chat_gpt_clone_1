$ErrorActionPreference = "Stop"

$ExpectedBranch = "security-accuracy-expansion-20260508"
$StageName = "github_visible_source_lineage_20260516"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = Resolve-Path (Join-Path $ScriptDir "..\..\..")
$MainRepo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$EvidenceDir = Join-Path $Repo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
$MainEvidenceDir = Join-Path $MainRepo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
New-Item -ItemType Directory -Force -Path $MainEvidenceDir | Out-Null

$Report = Join-Path $EvidenceDir "GITHUB_SNAPSHOT_APPLY_REPORT.txt"
$Blockers = Join-Path $EvidenceDir "GITHUB_SNAPSHOT_APPLY_BLOCKERS.md"
$PytestOut = Join-Path $EvidenceDir "GITHUB_SNAPSHOT_APPLY_PYTEST.txt"
$DiffCheckOut = Join-Path $EvidenceDir "GITHUB_SNAPSHOT_APPLY_DIFF_CHECK.txt"
$GitStatusOut = Join-Path $EvidenceDir "GITHUB_SNAPSHOT_APPLY_GIT_STATUS.txt"
$PublishLog = Join-Path $EvidenceDir "GITHUB_SNAPSHOT_APPLY_PUBLISH_LOG.txt"

$BlockerList = New-Object System.Collections.Generic.List[string]
$MovedFiles = New-Object System.Collections.Generic.List[string]
$BackupDir = Join-Path $EvidenceDir ("github_snapshot_apply_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

function Add-Blocker([string]$Name) {
  if (-not $BlockerList.Contains($Name)) { $BlockerList.Add($Name) }
}

function Copy-SnapshotFile {
  param(
    [string]$RelativePath
  )

  $Src = Join-Path $ScriptDir (Join-Path "source_snapshot" $RelativePath)
  $Dst = Join-Path $Repo $RelativePath
  $Backup = Join-Path $BackupDir $RelativePath

  if (!(Test-Path $Src)) {
    Add-Blocker "SNAPSHOT_FILE_MISSING:$RelativePath"
    return
  }

  New-Item -ItemType Directory -Force -Path (Split-Path $Dst), (Split-Path $Backup) | Out-Null
  if (Test-Path $Dst) {
    Copy-Item -LiteralPath $Dst -Destination $Backup -Force
  }
  Copy-Item -LiteralPath $Src -Destination $Dst -Force
  $MovedFiles.Add($RelativePath)
}

Set-Location $Repo
$Branch = (git branch --show-current).Trim()
$HeadBefore = (git rev-parse --short=12 HEAD).Trim()

if ($Branch -ne $ExpectedBranch) {
  Add-Blocker "BRANCH_MISMATCH:$Branch"
}

if ($BlockerList.Count -eq 0) {
  Copy-SnapshotFile "app\etl\match\parcel_matcher.py"
  Copy-SnapshotFile "tests\test_parcel_matcher_source_confidence.py"
}

if ($BlockerList.Count -eq 0) {
  $DiffCheckText = git diff --check -- "app/etl/match/parcel_matcher.py" "tests/test_parcel_matcher_source_confidence.py" 2>&1
  $DiffCheckExit = $LASTEXITCODE
  @(
    "diff_check_exit_code=$DiffCheckExit",
    "",
    $DiffCheckText
  ) | Set-Content -LiteralPath $DiffCheckOut -Encoding UTF8
  if ($DiffCheckExit -ne 0) { Add-Blocker "DIFF_CHECK_FAILED" }
} else {
  $DiffCheckExit = $null
}

if ($BlockerList.Count -eq 0) {
  $PytestTargets = @(
    "tests/test_parcel_matcher_source_confidence.py",
    "tests/test_source_confidence_integration.py",
    "tests/test_source_confidence_rules.py"
  )
  $PytestCmd = @("python", "-m", "pytest") + $PytestTargets + @("-q")
  $PytestOutput = & $PytestCmd[0] $PytestCmd[1..($PytestCmd.Count-1)] 2>&1
  $PytestExit = $LASTEXITCODE
  @(
    "pytest_exit_code=$PytestExit",
    "cmd=$($PytestCmd -join ' ')",
    "",
    $PytestOutput
  ) | Set-Content -LiteralPath $PytestOut -Encoding UTF8
  if ($PytestExit -ne 0) { Add-Blocker "TARGETED_PYTEST_FAILED" }
} else {
  $PytestExit = $null
}

$CommitStatus = "not_attempted"
$PushStatus = "not_attempted"
$CommitHash = ""

if ($BlockerList.Count -eq 0) {
  git status --short | Set-Content -LiteralPath $GitStatusOut -Encoding UTF8
  git add "app/etl/match/parcel_matcher.py" "tests/test_parcel_matcher_source_confidence.py" `
    "docs/chatgpt_handoff/parcel_location_evidence_wave_20260516/GITHUB_SNAPSHOT_APPLY_REPORT.txt" `
    "docs/chatgpt_handoff/parcel_location_evidence_wave_20260516/GITHUB_SNAPSHOT_APPLY_BLOCKERS.md" `
    "docs/chatgpt_handoff/parcel_location_evidence_wave_20260516/GITHUB_SNAPSHOT_APPLY_PYTEST.txt" `
    "docs/chatgpt_handoff/parcel_location_evidence_wave_20260516/GITHUB_SNAPSHOT_APPLY_DIFF_CHECK.txt" `
    "docs/chatgpt_handoff/parcel_location_evidence_wave_20260516/GITHUB_SNAPSHOT_APPLY_GIT_STATUS.txt" `
    "docs/chatgpt_handoff/parcel_location_evidence_wave_20260516/GITHUB_SNAPSHOT_APPLY_PUBLISH_LOG.txt" 2>&1 | Tee-Object -FilePath $PublishLog

  $CachedFiles = git diff --cached --name-only
  if (-not $CachedFiles) {
    $CommitStatus = "nothing_to_commit"
  } else {
    git commit -m "Apply source lineage guard from ChatGPT handoff" 2>&1 | Tee-Object -FilePath $PublishLog -Append
    if ($LASTEXITCODE -eq 0) {
      $CommitStatus = "committed"
      $CommitHash = (git rev-parse --short=12 HEAD).Trim()
      git push origin $Branch 2>&1 | Tee-Object -FilePath $PublishLog -Append
      if ($LASTEXITCODE -eq 0) {
        $PushStatus = "pushed"
      } else {
        $PushStatus = "push_failed"
        Add-Blocker "GIT_PUSH_FAILED"
      }
    } else {
      $CommitStatus = "commit_failed"
      Add-Blocker "GIT_COMMIT_FAILED"
    }
  }
}

$HeadAfter = (git rev-parse --short=12 HEAD).Trim()
$Final = if ($BlockerList.Count -eq 0) { "SOURCE_LINEAGE_APPLICATION_APPLY_READY" } else { "BLOCKED" }
$Next = if ($Final -eq "SOURCE_LINEAGE_APPLICATION_APPLY_READY") { "run_api_smoke_and_copy_to_main_repo_if_needed" } else { $BlockerList[0] }

@(
  "timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
  "task=GITHUB_SNAPSHOT_APPLY_TO_APPLICATION",
  "repo=$Repo",
  "main_repo=$MainRepo",
  "branch=$Branch",
  "head_before=$HeadBefore",
  "head_after=$HeadAfter",
  "moved_files=$($MovedFiles -join '; ')",
  "backup_dir=$BackupDir",
  "diff_check_exit_code=$DiffCheckExit",
  "pytest_exit_code=$PytestExit",
  "pytest_output=$PytestOut",
  "diff_check_output=$DiffCheckOut",
  "git_status_output=$GitStatusOut",
  "commit_status=$CommitStatus",
  "commit_hash=$CommitHash",
  "push_status=$PushStatus",
  "db_write=none",
  "ddl=none",
  "migration_apply=none",
  "prod_deploy=none",
  "secret_values_printed=false",
  "final_classification=$Final",
  "next_single_action=$Next"
) | Set-Content -LiteralPath $Report -Encoding UTF8

$BlockerLines = @("# GitHub Snapshot Apply Blockers", "")
if ($BlockerList.Count -eq 0) {
  $BlockerLines += "- none"
} else {
  foreach ($b in $BlockerList) { $BlockerLines += "- $b" }
}
$BlockerLines | Set-Content -LiteralPath $Blockers -Encoding UTF8

# Mirror reports to the main application folder for easier collection.
Copy-Item -LiteralPath $Report -Destination (Join-Path $MainEvidenceDir "GITHUB_SNAPSHOT_APPLY_REPORT.txt") -Force
Copy-Item -LiteralPath $Blockers -Destination (Join-Path $MainEvidenceDir "GITHUB_SNAPSHOT_APPLY_BLOCKERS.md") -Force
Copy-Item -LiteralPath $PytestOut -Destination (Join-Path $MainEvidenceDir "GITHUB_SNAPSHOT_APPLY_PYTEST.txt") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $DiffCheckOut -Destination (Join-Path $MainEvidenceDir "GITHUB_SNAPSHOT_APPLY_DIFF_CHECK.txt") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $PublishLog -Destination (Join-Path $MainEvidenceDir "GITHUB_SNAPSHOT_APPLY_PUBLISH_LOG.txt") -Force -ErrorAction SilentlyContinue

Get-Content $Report
Write-Host ""
Get-Content $Blockers
