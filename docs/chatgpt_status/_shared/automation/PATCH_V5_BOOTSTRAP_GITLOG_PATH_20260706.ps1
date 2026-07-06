[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738"
)

$ErrorActionPreference = "Stop"
$runner = Join-Path $RepoRoot "docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1"
if (!(Test-Path -LiteralPath $runner)) { throw "Runner not found: $runner" }

$text = Get-Content -LiteralPath $runner -Raw
if ($text -match "AAYS_V5_bootstrap_logs") {
  Write-Output "PATCH_ALREADY_PRESENT=true"
  exit 0
}

$old = @'
function Invoke-Git {
  param([Parameter(Mandatory=$true)][string]$Cwd,[Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  if ($null -eq $Args -or $Args.Count -eq 0) { throw "BLOCKED_BARE_GIT_USAGE" }
  Ensure-Dir (Split-Path -Parent $script:GitLogPath)
  Add-Content -LiteralPath $script:GitLogPath -Encoding UTF8 -Value ("[{0}] cwd={1} git {2}" -f (Now-Utc), $Cwd, ($Args -join ' '))
  Push-Location -LiteralPath $Cwd
'@

$new = @'
function Invoke-Git {
  param([Parameter(Mandatory=$true)][string]$Cwd,[Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  if ([string]::IsNullOrWhiteSpace($Cwd)) { throw "INVOKE_GIT_CWD_EMPTY" }
  if ($null -eq $Args -or $Args.Count -eq 0) { throw "BLOCKED_BARE_GIT_USAGE" }
  if ([string]::IsNullOrWhiteSpace($script:GitLogPath)) {
    $bootstrapLogDir = Join-Path $env:TEMP "AAYS_V5_bootstrap_logs"
    Ensure-Dir $bootstrapLogDir
    $script:GitLogPath = Join-Path $bootstrapLogDir ("MULTI_PAGE_git_args_V5_bootstrap_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
  }
  Ensure-Dir (Split-Path -Parent $script:GitLogPath)
  Add-Content -LiteralPath $script:GitLogPath -Encoding UTF8 -Value ("[{0}] cwd={1} git {2}" -f (Now-Utc), $Cwd, ($Args -join ' '))
  Push-Location -LiteralPath $Cwd
'@

if (-not $text.Contains($old)) { throw "Expected Invoke-Git block not found; inspect runner before patching." }
$text = $text.Replace($old, $new)
[System.IO.File]::WriteAllText($runner, $text, [System.Text.UTF8Encoding]::new($false))

# Basic syntax guard: no merge markers and runner contains bootstrap log fallback.
$patched = Get-Content -LiteralPath $runner -Raw
if ($patched -match "<<<<<<<|=======|>>>>>>>") { throw "Runner still contains merge conflict markers." }
if ($patched -notmatch "AAYS_V5_bootstrap_logs") { throw "Bootstrap log fallback not applied." }
Write-Output "PATCHED_V5_BOOTSTRAP_GITLOG_PATH=true"
Write-Output "PATCHED_FILE=$runner"
