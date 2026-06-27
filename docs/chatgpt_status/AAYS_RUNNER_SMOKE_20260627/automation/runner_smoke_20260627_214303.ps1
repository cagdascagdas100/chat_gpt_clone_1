param(
  [string]$TaskId,
  [string]$ResultPath,
  [string]$RepoResultPath
)

$ErrorActionPreference = 'Stop'
$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main'
$PageKey = 'AAYS_RUNNER_SMOKE_20260627'
$RepoOutputPath = 'F:\chatgpt\chat_gpt_clone_1_main\docs\chatgpt_status\AAYS_RUNNER_SMOKE_20260627\runner_outputs\runner_smoke_20260627_214303.output.txt'
$StatusPath = 'F:\chatgpt\chat_gpt_clone_1_main\docs\chatgpt_status\AAYS_RUNNER_SMOKE_20260627\status\runner_smoke_20260627_214303.status.json'
$HeartbeatPath = 'F:\chatgpt\chat_gpt_clone_1_main\docs\chatgpt_status\AAYS_RUNNER_SMOKE_20260627\heartbeat\runner_smoke_20260627_214303.heartbeat.txt'
$DoPush = $false
$now = Get-Date -Format s

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $RepoResultPath),(Split-Path -Parent $ResultPath),(Split-Path -Parent $RepoOutputPath),(Split-Path -Parent $StatusPath),(Split-Path -Parent $HeartbeatPath) | Out-Null

$bodyLines = @(
  "page_key=$PageKey",
  "task_id=$TaskId",
  "runner_pickup=proven",
  "runner_script_execution=proven",
  "runner_push=not_requested",
  "final_ready=false",
  "db_write=false",
  "ddl=false",
  "migration=false",
  "production_deploy=false",
  "fake_data=false",
  "executed_at=$now"
)
$body = $bodyLines -join [Environment]::NewLine

Set-Content -LiteralPath $RepoResultPath -Value $body -Encoding UTF8
Set-Content -LiteralPath $ResultPath -Value $body -Encoding UTF8
Set-Content -LiteralPath $RepoOutputPath -Value $body -Encoding UTF8
Set-Content -LiteralPath $HeartbeatPath -Value "task_id=$TaskId`nstatus=runner_smoke_executed`ntime=$now" -Encoding UTF8

$status = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  runner_pickup = 'proven'
  runner_script_execution = 'proven'
  runner_push = 'not_requested'
  final_ready = $false
  db_write = $false
  ddl = $false
  migration = $false
  production_deploy = $false
  fake_data = $false
  executed_at = $now
}

if ($DoPush) {
  try {
    git -C $RepoRoot branch --show-current | Out-Null
    git -C $RepoRoot add -- "docs/chatgpt_status/$PageKey"
    $pending = git -C $RepoRoot status --short -- "docs/chatgpt_status/$PageKey"
    if ($pending) {
      git -C $RepoRoot commit -m "test $PageKey runner smoke proof $TaskId" | Out-Null
      git -C $RepoRoot push origin main | Out-Null
      $status.runner_push = 'proven'
      (Get-Content -LiteralPath $RepoResultPath -Raw).Replace('runner_push=not_requested','runner_push=proven') | Set-Content -LiteralPath $RepoResultPath -Encoding UTF8
    } else {
      $status.runner_push = 'nothing_to_commit'
    }
  } catch {
    $status.runner_push = 'not_proven'
    $status.push_error = $_.Exception.Message
  }
}

$status | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $StatusPath -Encoding UTF8
exit 0
