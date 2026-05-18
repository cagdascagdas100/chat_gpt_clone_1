$ErrorActionPreference = "Continue"
$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
$Branch = "security-accuracy-expansion-20260508"
$OutDir = Join-Path $Repo "docs\chatgpt_handoff\cloud_ready_20260517"
$Report = Join-Path $OutDir "012B_LOCAL_TEST_SMOKE_PERF_REPORT.txt"
$PytestRaw = Join-Path $OutDir "012B_PYTEST_RAW.txt"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Set-Location $Repo
git fetch origin $Branch | Out-Null
git checkout $Branch | Out-Null
git pull --ff-only origin $Branch | Out-Null
$head = (git rev-parse --short=12 HEAD).Trim()
$pytestExit = "not_run"
$pytestStatus = "not_run"
if (Test-Path "tests") {
  python -m pytest tests/test_parcel_matcher_source_confidence.py tests/test_source_confidence_integration.py tests/test_source_confidence_rules.py -q *> $PytestRaw
  $pytestExit = $LASTEXITCODE
  $pytestStatus = if($pytestExit -eq 0){"passed"}else{"failed"}
} else {
  "tests_dir_missing" | Set-Content -LiteralPath $PytestRaw -Encoding UTF8
  $pytestExit = 999
  $pytestStatus = "failed"
}
$blockers = if($pytestStatus -eq "passed"){"api_smoke_not_run;perf_not_run"}else{"pytest_failed;api_smoke_not_run;perf_not_run"}
@(
"timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
"task=012B_LOCAL_TEST_SMOKE_PERF",
"report_type=actual_runner_output_partial",
"checked_branch=$Branch",
"head=$head",
"pytest_status=$pytestStatus",
"pytest_exit_code=$pytestExit",
"pytest_output=$PytestRaw",
"api_smoke_status=not_run",
"perf_status=not_run",
"public_url_verified=false",
"cloud_db_verified=false",
"classification_recommendation=CLOUD_READY_PENDING_PROVIDER",
"next_single_action=WAIT_FOR_USER_PROVIDER_DECISION",
"blockers=$blockers",
"secret_values_printed=false",
"db_write=none",
"ddl=none",
"migration_apply=none",
"prod_deploy=none"
) | Set-Content -LiteralPath $Report -Encoding UTF8
git add "docs/chatgpt_handoff/cloud_ready_20260517" | Out-Null
if(git diff --cached --name-only){ git commit -m "Publish actual 012B local test report" | Out-Null; if($LASTEXITCODE -eq 0){ git push origin $Branch | Out-Null } }
Get-Content $Report
