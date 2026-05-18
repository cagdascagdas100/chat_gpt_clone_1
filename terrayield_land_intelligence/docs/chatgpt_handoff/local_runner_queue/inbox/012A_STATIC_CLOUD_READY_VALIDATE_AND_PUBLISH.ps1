$ErrorActionPreference = "Continue"
$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
$Branch = "security-accuracy-expansion-20260508"
$OutDir = Join-Path $Repo "docs\chatgpt_handoff\cloud_ready_20260517"
$Report = Join-Path $OutDir "012A_STATIC_CLOUD_READY_VALIDATE_REPORT.txt"
$Raw = Join-Path $OutDir "012A_STATIC_CLOUD_READY_VALIDATE_RAW.txt"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Set-Location $Repo
git fetch origin $Branch | Out-Null
git checkout $Branch | Out-Null
git pull --ff-only origin $Branch | Out-Null
$head = (git rev-parse --short=12 HEAD).Trim()
$validator = "scripts\validate_cloud_readiness_static.py"
$exit = "not_run"
if (Test-Path $validator) {
  python $validator *> $Raw
  $exit = $LASTEXITCODE
} else {
  "validator_missing" | Set-Content -LiteralPath $Raw -Encoding UTF8
  $exit = 999
}
$status = if($exit -eq 0){"passed"}else{"failed"}
$blockers = if($exit -eq 0){"none"}else{"static_validation_failed_or_missing"}
@(
"timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
"task=012A_STATIC_CLOUD_READY_VALIDATE",
"report_type=actual_runner_output",
"checked_branch=$Branch",
"head=$head",
"validation_status=$status",
"validator_exit_code=$exit",
"raw_output=$Raw",
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
if(git diff --cached --name-only){ git commit -m "Publish actual 012A static validation report" | Out-Null; if($LASTEXITCODE -eq 0){ git push origin $Branch | Out-Null } }
Get-Content $Report
