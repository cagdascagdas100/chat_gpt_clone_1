param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [int]$MaxTasks = 1
)

$ErrorActionPreference = 'Stop'
$runner = Join-Path $PSScriptRoot 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1'
if (-not (Test-Path -LiteralPath $runner)) { throw "Canonical shared runner not found: $runner" }
& $runner -RepoRoot $RepoRoot -MaxTasks $MaxTasks
exit $LASTEXITCODE