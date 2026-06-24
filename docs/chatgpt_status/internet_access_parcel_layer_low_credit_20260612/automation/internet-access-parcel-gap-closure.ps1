param(
  [string]$TaskId = "internet-access-parcel-gap-closure",
  [string]$ResultPath = "",
  [string]$RepoResultPath = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$PageKey = "internet_access_parcel_layer_low_credit_20260612"
$Base = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey"
$Reports = Join-Path $Base "reports"
$Status = Join-Path $Base "status"
$Heartbeat = Join-Path $Base "heartbeat"
$RunnerOutputs = Join-Path $Base "runner_outputs"
New-Item -ItemType Directory -Force -Path $Reports,$Status,$Heartbeat,$RunnerOutputs | Out-Null
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$statusFile = Join-Path $Status "internet-access-parcel-gap-closure-current-status.json"
$runnerMd = Join-Path $Reports "internet-access-runner-$ts.md"
$hb = Join-Path $Status "internet-access-runner-heartbeat-$ts.json"
$text = @"
PAGE_KEY=$PageKey
TASK_ID=$TaskId
STATUS=BLOCKED_MISSING_PRODUCT_GATES
FINAL_READY=false
runner_pickup=proven_local_only
runner_push=not_proven
blockers=missing_main_branch_push;missing_real_geometry_acceptance;missing_nonempty_runtime_feature_proof
"@
'{"status":"blocked","final_ready":false,"runner_pickup":"proven_local_only","runner_push":"not_proven"}' | Set-Content -LiteralPath $statusFile -Encoding UTF8
$text | Set-Content -LiteralPath $runnerMd -Encoding UTF8
("{""status"":""blocked"",""final_ready"":false,""task_id"":""$TaskId""}") | Set-Content -LiteralPath $hb -Encoding UTF8
if ($ResultPath) { $text | Set-Content -LiteralPath $ResultPath -Encoding UTF8 }
if ($RepoResultPath) { $text | Set-Content -LiteralPath $RepoResultPath -Encoding UTF8 }
Write-Output "internet blocker outputs written"
