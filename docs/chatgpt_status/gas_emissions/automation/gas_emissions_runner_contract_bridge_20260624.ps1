param(
  [string]$TaskId = "gas_emissions_runner_contract_bridge_20260624",
  [string]$ResultPath = "",
  [string]$RepoResultPath = ""
)

$ErrorActionPreference = "Stop"
$PageKey = "gas_emissions"

function Get-RepoRelativePath {
  param([string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
  $normalized = $Path -replace '/', '\'
  $markers = @("\docs\chatgpt_status\", "\tools\")
  foreach ($marker in $markers) {
    $idx = $normalized.IndexOf($marker, [System.StringComparison]::OrdinalIgnoreCase)
    if ($idx -ge 0) {
      return $normalized.Substring($idx + 1).TrimStart("\")
    }
  }
  return $normalized.TrimStart("\")
}

function Get-CanonicalRepoPath {
  param(
    [string]$Path,
    [string]$Root,
    [string]$FallbackRelative
  )
  if ([string]::IsNullOrWhiteSpace($Path)) {
    return (Join-Path $Root $FallbackRelative)
  }
  $relative = Get-RepoRelativePath $Path
  if ([System.IO.Path]::IsPathRooted($relative)) {
    return $relative
  }
  return (Join-Path $Root $relative)
}

$RepoRootHelper = Join-Path $PSScriptRoot "..\..\..\..\tools\Get-AaysRepoRoot.ps1"
if (Test-Path -LiteralPath $RepoRootHelper) {
  $RepoRoot = & $RepoRootHelper
} else {
  $RepoRoot = "F:\chatgpt\chat_gpt_clone_1_main"
}

$Base = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey"
$Reports = Join-Path $Base "reports"
$Heartbeat = Join-Path $Base "heartbeat"
$Status = Join-Path $Base "status"
New-Item -ItemType Directory -Force -Path $Reports,$Heartbeat,$Status | Out-Null
$ResultPath = Get-CanonicalRepoPath $ResultPath $RepoRoot "docs\chatgpt_status\$PageKey\reports\gas_emissions_finalizer_result_20260622_2300.md"
$RepoResultPath = Get-CanonicalRepoPath $RepoResultPath $RepoRoot "docs\chatgpt_status\$PageKey\reports\gas_emissions_finalizer_result_20260622_2300.md"
$text = @"
PAGE_KEY=$PageKey
TASK_ID=$TaskId
STATUS=BLOCKED_MAIN_BRANCH_PROOF
completion_percent=89
final_ready=false
runner_pickup=proven_local_only
runner_push=not_proven
blockers=local_checkout_not_main;finalizer_not_proven_on_main;page_key_root_evidence_not_pushed
"@
$resultParent = if ($ResultPath) { Split-Path -Parent $ResultPath } else { "" }
$repoResultParent = if ($RepoResultPath) { Split-Path -Parent $RepoResultPath } else { "" }
if ($resultParent) { New-Item -ItemType Directory -Force -Path $resultParent | Out-Null }
if ($repoResultParent) { New-Item -ItemType Directory -Force -Path $repoResultParent | Out-Null }
$text | Set-Content -LiteralPath (Join-Path $Reports "gas_emissions_finalizer_result_20260622_2300.md") -Encoding UTF8
$text | Set-Content -LiteralPath (Join-Path $Heartbeat "gas_emissions_runner_heartbeat_20260624.txt") -Encoding UTF8
$text | Set-Content -LiteralPath (Join-Path $Status "gas_emissions_runner_status_20260624.txt") -Encoding UTF8
if ($ResultPath) { $text | Set-Content -LiteralPath $ResultPath -Encoding UTF8 }
if ($RepoResultPath) { $text | Set-Content -LiteralPath $RepoResultPath -Encoding UTF8 }
Write-Output "gas emissions bridge blocker written"
