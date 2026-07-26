param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1',
  [string]$MainBranch = 'main',
  [int]$MaxTasks = 1,
  [int]$StaleMinutes = 20,
  [switch]$ScanOnly
)

$ErrorActionPreference = 'Stop'
$runner = Join-Path $PSScriptRoot 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1'
if (-not (Test-Path -LiteralPath $runner)) { throw "Canonical shared runner not found: $runner" }
if ($ScanOnly) {
  & $runner -RepoRoot $RepoRoot -RepoFullName $RepoFullName -MainBranch $MainBranch -MaxTasks $MaxTasks -StaleMinutes $StaleMinutes -ScanOnly
} else {
  & $runner -RepoRoot $RepoRoot -RepoFullName $RepoFullName -MainBranch $MainBranch -MaxTasks $MaxTasks -StaleMinutes $StaleMinutes
}
exit $LASTEXITCODE