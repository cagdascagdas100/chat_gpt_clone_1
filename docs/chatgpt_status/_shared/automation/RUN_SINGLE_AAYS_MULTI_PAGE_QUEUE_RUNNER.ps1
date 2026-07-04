param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1',
  [string]$MainBranch = 'main',
  [int]$StaleMinutes = 20,
  [int]$MaxTasks = 1
)

$ErrorActionPreference = 'Stop'
$launcher = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V2_LOCKED_20260704.ps1'
if (-not (Test-Path -LiteralPath $launcher)) {
  throw 'V2 locked launcher missing: ' + $launcher
}
& powershell -NoProfile -ExecutionPolicy Bypass -File $launcher -RepoRoot $RepoRoot -StaleMinutes $StaleMinutes
exit $LASTEXITCODE
