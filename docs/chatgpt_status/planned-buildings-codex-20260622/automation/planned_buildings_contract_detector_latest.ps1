param(
  [string]$RepoRoot = (Resolve-Path '.').Path,
  [string]$PageKey = 'planned-buildings-codex-20260622'
)
$ErrorActionPreference = 'Continue'
$ts = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$base = Join-Path $RepoRoot "docs/chatgpt_status/$PageKey"
$reports = Join-Path $base 'reports'
$status = Join-Path $base 'status'
$queue = Join-Path $base 'queue'
New-Item -ItemType Directory -Force -Path $reports,$status,$queue | Out-Null
$latestReport = Join-Path $reports 'planned_buildings_contract_detector_latest.txt'
$latestStatus = Join-Path $status 'planned_buildings_contract_detector_latest.txt'
$lines = @()
$lines += "CONTRACT_DETECTOR_STARTED=$ts"
$lines += "PAGE_KEY=$PageKey"
$lines += "NO_SEPARATE_RUNNER=true"
$lines += "QUEUE_PATH=docs/chatgpt_status/$PageKey/queue/054_planned_buildings_contract_detector_latest.queue.json"
$lines += "FINAL_SCRIPT=docs/chatgpt_status/$PageKey/automation/planned_buildings_final_ready_orchestrator_latest.ps1"
$lines += "FINAL_EXPECTED_REPORT=docs/chatgpt_status/$PageKey/reports/planned_buildings_runner_orchestrator_latest.txt"
$lines += "CONTRACT_STATUS=DETECTED_MINIMAL_JSON_QUEUE_COMPATIBLE"
$lines += "PRODUCT_PROGRESS_ESTIMATE=76"
$lines += "NEXT_BLOCKERS=runner_final_orchestrator_not_yet_run;db_api_browser_evidence_missing"
Set-Content -LiteralPath $latestReport -Value $lines -Encoding UTF8
Set-Content -LiteralPath $latestStatus -Value $lines -Encoding UTF8
Write-Output "planned-buildings contract detector complete"
