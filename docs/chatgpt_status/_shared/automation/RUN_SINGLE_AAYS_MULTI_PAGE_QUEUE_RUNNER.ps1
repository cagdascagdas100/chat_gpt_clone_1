param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1',
  [string]$MainBranch = 'main',
  [string]$WorkRoot = 'F:\AAYS_WT',
  [int]$StaleMinutes = 20,
  [int]$MaxTasks = 1,
  [switch]$ScanOnly
)

$ErrorActionPreference = 'Stop'
$runner = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V4_20260706.ps1'
if (-not (Test-Path -LiteralPath $runner)) {
  throw 'V4 shared runner missing: ' + $runner
}

$argsList = @(
  '-NoProfile',
  '-ExecutionPolicy', 'Bypass',
  '-File', $runner,
  '-RepoRoot', $RepoRoot,
  '-RepoFullName', $RepoFullName,
  '-MainBranch', $MainBranch,
  '-WorkRoot', $WorkRoot,
  '-StaleMinutes', ([string]$StaleMinutes),
  '-MaxTasks', ([string]$MaxTasks)
)
if ($ScanOnly) { $argsList += '-ScanOnly' }

& powershell @argsList
exit $LASTEXITCODE
