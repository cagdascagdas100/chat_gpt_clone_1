$ErrorActionPreference = "Continue"

$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Branch = "security-accuracy-expansion-20260508"
$OutDir = Join-Path $Repo "docs\chatgpt_handoff\cloud_ready_20260517"
$QueueOut = Join-Path $Repo "docs\chatgpt_handoff\local_runner_queue\outputs"
$Report = Join-Path $OutDir "013_WATCHDOG_SAFE_ONCE_REPORT.txt"
$Blockers = Join-Path $OutDir "013_WATCHDOG_SAFE_ONCE_BLOCKERS.md"
$StartWrapper = Join-Path $Repo "docs\chatgpt_handoff\local_runner_queue\START_WATCHDOG_SAFE_ONCE.ps1"

New-Item -ItemType Directory -Force -Path $OutDir,$QueueOut | Out-Null
Set-Location $Repo

$B = New-Object System.Collections.Generic.List[string]
function AB($x){ if(-not $B.Contains($x)){ $B.Add($x) } }

$branchBefore = (git branch --show-current).Trim()
git fetch origin $Branch | Out-Null
git checkout $Branch | Out-Null
git pull --ff-only origin $Branch | Out-Null
$branchAfter = (git branch --show-current).Trim()
$head = (git rev-parse --short=12 HEAD).Trim()

if($branchAfter -ne $Branch){ AB "branch_mismatch" }
if(!(Test-Path $StartWrapper)){ AB "start_wrapper_missing" }

$wrapperExit = "not_run"
if($B.Count -eq 0){
  powershell -ExecutionPolicy Bypass -File $StartWrapper | Tee-Object -FilePath (Join-Path $QueueOut "013_START_WRAPPER_OUTPUT.txt")
  $wrapperExit = $LASTEXITCODE
  if($LASTEXITCODE -ne 0){ AB "start_wrapper_failed" }
}

$Heartbeat = Join-Path $QueueOut "WATCHDOG_HEARTBEAT.txt"
$R012A = Join-Path $OutDir "012A_STATIC_CLOUD_READY_VALIDATE_REPORT.txt"
$R012B = Join-Path $OutDir "012B_LOCAL_TEST_SMOKE_PERF_REPORT.txt"

$heartbeatVisible = Test-Path $Heartbeat
$r012aVisible = Test-Path $R012A
$r012bVisible = Test-Path $R012B

$final = if($B.Count -eq 0){"CLOUD_READY_PENDING_PROVIDER"}else{"BLOCKED"}
$next = if($B.Count -eq 0){"WAIT_FOR_USER_PROVIDER_DECISION"}else{$B[0]}

@(
"timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
"task=013_RUN_WATCHDOG_SAFE_ONCE_AND_PUBLISH",
"branch_before=$branchBefore",
"checked_branch=$branchAfter",
"head=$head",
"wrapper_exit=$wrapperExit",
"heartbeat_visible=$heartbeatVisible",
"012a_report_visible=$r012aVisible",
"012b_report_visible=$r012bVisible",
"public_url_verified=false",
"cloud_db_verified=false",
"final_classification=$final",
"next_single_action=$next",
"secret_values_printed=false",
"db_write=none",
"ddl=none",
"migration_apply=none",
"prod_deploy=none",
"blockers=$(if($B.Count -eq 0){'none'}else{($B -join ';')})"
) | Set-Content -LiteralPath $Report -Encoding UTF8

$BL=@("# 013 Watchdog Safe Once Blockers","")
if($B.Count -eq 0){$BL += "- none"}else{foreach($x in $B){$BL += "- $x"}}
$BL | Set-Content -LiteralPath $Blockers -Encoding UTF8

git add "docs/chatgpt_handoff" "docs/cloud_ready" | Out-Null
if(git diff --cached --name-only){
  git commit -m "Publish 013 watchdog safe once evidence" | Out-Null
  if($LASTEXITCODE -eq 0){ git push origin $Branch | Out-Null }
}

Get-Content $Report
