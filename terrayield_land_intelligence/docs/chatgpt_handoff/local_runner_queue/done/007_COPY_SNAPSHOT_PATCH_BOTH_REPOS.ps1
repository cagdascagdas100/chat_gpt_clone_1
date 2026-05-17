$ErrorActionPreference = "Continue"

$TaskName = "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS"
$ExpectedBranch = "security-accuracy-expansion-20260508"
$CorrectRepo = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
$MainRepo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$EvidenceDir = Join-Path $CorrectRepo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
$MainEvidenceDir = Join-Path $MainRepo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
$StageDir = Join-Path $CorrectRepo "docs\chatgpt_handoff\github_visible_source_lineage_20260516"
New-Item -ItemType Directory -Force -Path $EvidenceDir, $MainEvidenceDir | Out-Null

$Report = Join-Path $EvidenceDir "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_REPORT.txt"
$Blockers = Join-Path $EvidenceDir "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_BLOCKERS.md"
$PytestOut = Join-Path $EvidenceDir "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_PYTEST.txt"
$ImportProbeOut = Join-Path $EvidenceDir "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_IMPORT_PROBE.txt"
$DiffCheckOut = Join-Path $EvidenceDir "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_DIFF_CHECK.txt"
$PublishLog = Join-Path $EvidenceDir "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_PUBLISH_LOG.txt"
$StatusOut = Join-Path $EvidenceDir "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_STATUS.txt"
$BlockerList = New-Object System.Collections.Generic.List[string]
$Moved = New-Object System.Collections.Generic.List[string]

function Add-Blocker([string]$Name) { if (-not $BlockerList.Contains($Name)) { $BlockerList.Add($Name) } }
function Copy-ExactFile([string]$Source, [string]$Dest, [string]$Label) {
  if (!(Test-Path $Source)) { Add-Blocker "SOURCE_MISSING:$Label"; return }
  New-Item -ItemType Directory -Force -Path (Split-Path $Dest) | Out-Null
  Copy-Item -LiteralPath $Source -Destination $Dest -Force
  $Moved.Add($Label)
}

Set-Location $CorrectRepo
$Branch = (git branch --show-current).Trim()
$HeadBefore = (git rev-parse --short=12 HEAD).Trim()
if ($Branch -ne $ExpectedBranch) { Add-Blocker "BRANCH_MISMATCH:$Branch" }

$PullOutput = git pull origin $ExpectedBranch 2>&1
$PullExit = $LASTEXITCODE
if ($PullExit -ne 0) { Add-Blocker "GIT_PULL_FAILED" }

$SnapshotMatcher = Join-Path $StageDir "source_snapshot\app\etl\match\parcel_matcher.py"
$SnapshotTest = Join-Path $StageDir "source_snapshot\tests\test_parcel_matcher_source_confidence.py"

if ($BlockerList.Count -eq 0) {
  Copy-ExactFile $SnapshotMatcher (Join-Path $CorrectRepo "app\etl\match\parcel_matcher.py") "correct_repo:app/etl/match/parcel_matcher.py"
  Copy-ExactFile $SnapshotMatcher (Join-Path $MainRepo "app\etl\match\parcel_matcher.py") "main_repo:app/etl/match/parcel_matcher.py"
  Copy-ExactFile $SnapshotTest (Join-Path $CorrectRepo "tests\test_parcel_matcher_source_confidence.py") "correct_repo:tests/test_parcel_matcher_source_confidence.py"
  Copy-ExactFile $SnapshotTest (Join-Path $MainRepo "tests\test_parcel_matcher_source_confidence.py") "main_repo:tests/test_parcel_matcher_source_confidence.py"
}

$ImportExit = $null
if ($BlockerList.Count -eq 0) {
  $oldPy = $env:PYTHONPATH
  $env:PYTHONPATH = "$MainRepo;$CorrectRepo"
  Set-Location $CorrectRepo
  $ImportOutput = python -c "import inspect; import app.etl.match.parcel_matcher as m; print(m.__file__); print('source_lineage_status' in inspect.getsource(m._build_match_source_confidence_fields)); print(inspect.getsource(m._build_match_source_confidence_fields))" 2>&1
  $ImportExit = $LASTEXITCODE
  $env:PYTHONPATH = $oldPy
  @(
    "import_exit_code=$ImportExit",
    "PYTHONPATH_ORDER=$MainRepo;$CorrectRepo",
    "",
    $ImportOutput
  ) | Set-Content -LiteralPath $ImportProbeOut -Encoding UTF8
  if ($ImportExit -ne 0) { Add-Blocker "IMPORT_PROBE_FAILED" }
  elseif (-not (($ImportOutput -join "`n") -match "(?m)^True$")) { Add-Blocker "IMPORT_PROBE_SOURCE_LINEAGE_MISSING" }
}

$DiffCheckExit = $null
if ($BlockerList.Count -eq 0) {
  Set-Location $CorrectRepo
  $DiffCheckText = git diff --check -- "app/etl/match/parcel_matcher.py" "tests/test_parcel_matcher_source_confidence.py" 2>&1
  $DiffCheckExit = $LASTEXITCODE
  @("diff_check_exit_code=$DiffCheckExit", "", $DiffCheckText) | Set-Content -LiteralPath $DiffCheckOut -Encoding UTF8
  if ($DiffCheckExit -ne 0) { Add-Blocker "DIFF_CHECK_FAILED" }
}

$PytestExit = $null
if ($BlockerList.Count -eq 0) {
  $oldPy = $env:PYTHONPATH
  $env:PYTHONPATH = "$MainRepo;$CorrectRepo"
  Set-Location $CorrectRepo
  $PytestOutput = python -m pytest tests/test_parcel_matcher_source_confidence.py tests/test_source_confidence_integration.py tests/test_source_confidence_rules.py -q 2>&1
  $PytestExit = $LASTEXITCODE
  $env:PYTHONPATH = $oldPy
  @(
    "pytest_exit_code=$PytestExit",
    "PYTHONPATH_ORDER=$MainRepo;$CorrectRepo",
    "cmd=python -m pytest tests/test_parcel_matcher_source_confidence.py tests/test_source_confidence_integration.py tests/test_source_confidence_rules.py -q",
    "",
    $PytestOutput
  ) | Set-Content -LiteralPath $PytestOut -Encoding UTF8
  if ($PytestExit -ne 0) { Add-Blocker "TARGETED_PYTEST_FAILED" }
}

$CommitStatus = "not_attempted"
$PushStatus = "not_attempted"
$CommitHash = ""
if ($BlockerList.Count -eq 0) {
  Set-Location $CorrectRepo
  git add "app/etl/match/parcel_matcher.py" "tests/test_parcel_matcher_source_confidence.py" 2>&1 | Tee-Object -FilePath $PublishLog
  $Cached = git diff --cached --name-only
  if ($Cached) {
    git commit -m "Apply source lineage guard from snapshot" 2>&1 | Tee-Object -FilePath $PublishLog -Append
    if ($LASTEXITCODE -eq 0) {
      $CommitStatus = "committed"
      $CommitHash = (git rev-parse --short=12 HEAD).Trim()
      git push origin $Branch 2>&1 | Tee-Object -FilePath $PublishLog -Append
      if ($LASTEXITCODE -eq 0) { $PushStatus = "pushed" } else { $PushStatus = "push_failed"; Add-Blocker "GIT_PUSH_FAILED" }
    } else {
      $CommitStatus = "commit_failed"
      Add-Blocker "GIT_COMMIT_FAILED"
    }
  } else {
    $CommitStatus = "nothing_to_commit"
  }
}

Set-Location $CorrectRepo
$HeadAfter = (git rev-parse --short=12 HEAD).Trim()
$Final = if ($BlockerList.Count -eq 0) { "COPY_SNAPSHOT_PATCH_BOTH_REPOS_READY" } else { "BLOCKED" }
$Next = if ($Final -eq "COPY_SNAPSHOT_PATCH_BOTH_REPOS_READY") { "queue_api_smoke_and_final_sync" } else { $BlockerList[0] }

@(
  "timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
  "task=$TaskName",
  "correct_repo=$CorrectRepo",
  "main_repo=$MainRepo",
  "branch=$Branch",
  "head_before=$HeadBefore",
  "head_after=$HeadAfter",
  "git_pull_exit_code=$PullExit",
  "moved_files=$($Moved -join '; ')",
  "import_exit_code=$ImportExit",
  "import_probe_output=$ImportProbeOut",
  "diff_check_exit_code=$DiffCheckExit",
  "diff_check_output=$DiffCheckOut",
  "pytest_exit_code=$PytestExit",
  "pytest_output=$PytestOut",
  "commit_status=$CommitStatus",
  "commit_hash=$CommitHash",
  "push_status=$PushStatus",
  "publish_log=$PublishLog",
  "db_write=none",
  "ddl=none",
  "migration_apply=none",
  "prod_deploy=none",
  "secret_values_printed=false",
  "final_classification=$Final",
  "next_single_action=$Next"
) | Set-Content -LiteralPath $Report -Encoding UTF8

$BlockerLines = @("# 007 Copy Snapshot Patch Both Repos Blockers", "")
if ($BlockerList.Count -eq 0) { $BlockerLines += "- none" } else { foreach ($b in $BlockerList) { $BlockerLines += "- $b" } }
$BlockerLines | Set-Content -LiteralPath $Blockers -Encoding UTF8

@(
  "task=$TaskName",
  "final_classification=$Final",
  "next_single_action=$Next",
  "report=$Report",
  "blockers=$Blockers"
) | Set-Content -LiteralPath $StatusOut -Encoding UTF8

Copy-Item -LiteralPath $Report -Destination (Join-Path $MainEvidenceDir "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_REPORT.txt") -Force
Copy-Item -LiteralPath $Blockers -Destination (Join-Path $MainEvidenceDir "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_BLOCKERS.md") -Force
Copy-Item -LiteralPath $PytestOut -Destination (Join-Path $MainEvidenceDir "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_PYTEST.txt") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $ImportProbeOut -Destination (Join-Path $MainEvidenceDir "007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_IMPORT_PROBE.txt") -Force -ErrorAction SilentlyContinue

# Always publish reports to GitHub.
Set-Location $CorrectRepo
git add "docs/chatgpt_handoff/parcel_location_evidence_wave_20260516" `
  "docs/chatgpt_handoff/local_runner_queue/done" `
  "docs/chatgpt_handoff/local_runner_queue/failed" `
  "docs/chatgpt_handoff/local_runner_queue/outputs" 2>&1 | Tee-Object -FilePath $PublishLog -Append
$CachedReports = git diff --cached --name-only
if ($CachedReports -and $CommitStatus -ne "committed") {
  git commit -m "Publish snapshot copy source lineage runner reports" 2>&1 | Tee-Object -FilePath $PublishLog -Append
  if ($LASTEXITCODE -eq 0) { git push origin $Branch 2>&1 | Tee-Object -FilePath $PublishLog -Append }
}

Get-Content $Report
Write-Host ""
Get-Content $Blockers
