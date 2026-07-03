param(
  [string]$RepoRoot = "",
  [string]$CleanRepo = "C:\Users\cagda\Documents\GitHub\AAYS_gas_emissions_mainbase_20260703",
  [string]$Branch = "gas-emissions-runner-evidence-mainbase-20260703"
)

$ErrorActionPreference = "Continue"
$RepoFullName = "cagdascagdas100/chat_gpt_clone_1"
$RepoUrl = "https://github.com/$RepoFullName.git"

function Say($m, $c="White") { Write-Host $m -ForegroundColor $c }
function EnsureDir($p) { if (!(Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null } }
function NowUtc { (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") }
function ReadJson($p) { try { if (Test-Path -LiteralPath $p) { return Get-Content -LiteralPath $p -Raw | ConvertFrom-Json } } catch {}; return $null }
function RunGit([string[]]$Args) {
  $out = & git @Args 2>&1
  [pscustomobject]@{ code=$LASTEXITCODE; output=($out -join "`n"); args=($Args -join " ") }
}

if (!$RepoRoot) {
  try { $RepoRoot = (& git rev-parse --show-toplevel 2>$null) } catch {}
  if (!$RepoRoot) { $RepoRoot = (Resolve-Path ".").Path }
}

$SourceGasRoot = Join-Path $RepoRoot "docs\chatgpt_status\gas_emissions"
$SourceStatusDir = Join-Path $SourceGasRoot "status"
$SourceReportDir = Join-Path $SourceGasRoot "reports"
EnsureDir $SourceStatusDir; EnsureDir $SourceReportDir

$started = NowUtc
Say "=== AAYS GAS EMISSIONS AUTONOMOUS CONTINUE RUNNER ===" Cyan
Say "repo_root=$RepoRoot" Cyan
Say "clean_repo=$CleanRepo" Cyan
Say "branch=$Branch" Cyan

$state = [ordered]@{
  runner_installed = $true
  runner_version = "20260704_github_autonomous"
  started_at = $started
  repo_root = $RepoRoot
  clean_repo = $CleanRepo
  branch = $Branch
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  steps = @()
  final_ready = $false
  post_sync_ok = $false
}

try {
  if (!(Test-Path -LiteralPath $CleanRepo)) {
    $parent = Split-Path -Parent $CleanRepo
    EnsureDir $parent
    $clone = RunGit @("clone", $RepoUrl, $CleanRepo)
    $state.steps += [ordered]@{ step="clone_clean_repo"; code=$clone.code; output=$clone.output }
    if ($clone.code -ne 0) { throw "clone failed: $($clone.output)" }
  }

  Push-Location $CleanRepo
  try {
    $fetch = RunGit @("fetch", "origin", $Branch)
    $state.steps += [ordered]@{ step="fetch_branch"; code=$fetch.code; output=$fetch.output }
    if ($fetch.code -ne 0) { throw "fetch failed: $($fetch.output)" }

    $current = (& git branch --show-current 2>$null)
    if ($current -ne $Branch) {
      $checkout = RunGit @("checkout", $Branch)
      if ($checkout.code -ne 0) { $checkout = RunGit @("checkout", "-B", $Branch, "origin/$Branch") }
      $state.steps += [ordered]@{ step="checkout_branch"; code=$checkout.code; output=$checkout.output }
      if ($checkout.code -ne 0) { throw "checkout failed: $($checkout.output)" }
    }

    $bridge = Join-Path $CleanRepo "docs\chatgpt_status\gas_emissions\automation\gas_emissions_single_runner_bridge_20260703.ps1"
    if (Test-Path -LiteralPath $bridge) {
      $env:AAYS_REPO_ROOT = $CleanRepo
      $bridgeOut = powershell -NoProfile -ExecutionPolicy Bypass -File $bridge 2>&1
      $bridgeCode = $LASTEXITCODE
      $state.steps += [ordered]@{ step="bridge"; code=$bridgeCode; output=($bridgeOut -join "`n") }
    } else {
      $state.steps += [ordered]@{ step="bridge"; code=2; output="missing bridge script" }
    }

    $EvidenceStatusDir = Join-Path $CleanRepo "docs\chatgpt_status\gas_emissions\status"
    EnsureDir $EvidenceStatusDir
    $state.completed_at = NowUtc
    $stateFileInClean = Join-Path $EvidenceStatusDir "aays_continue_runner_autonomous_state_20260704.json"
    $state | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $stateFileInClean -Encoding UTF8

    $paths = @(
      "docs/chatgpt_status/gas_emissions/status/aays_continue_runner_autonomous_state_20260704.json",
      "docs/chatgpt_status/gas_emissions/status/gas_emissions_current_status_20260703.txt",
      "docs/chatgpt_status/gas_emissions/reports/gas_emissions_progress_latest_20260703.md",
      "docs/chatgpt_status/gas_emissions/heartbeat/gas_emissions_single_runner_bridge_20260703_heartbeat.txt",
      "outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/latest_changes.json"
    )
    foreach ($p in $paths) { if (Test-Path -LiteralPath $p) { git add -f $p } }
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
      $commit = RunGit @("commit", "-m", "Gas Emissions autonomous continue runner state")
      $state.steps += [ordered]@{ step="commit_state"; code=$commit.code; output=$commit.output }
    }

    $fetch2 = RunGit @("fetch", "origin", $Branch)
    if ($fetch2.code -ne 0) { throw "post fetch failed: $($fetch2.output)" }
    $rebase2 = RunGit @("rebase", "origin/$Branch")
    if ($rebase2.code -ne 0) { git rebase --abort | Out-Null 2>&1; throw "post rebase failed: $($rebase2.output)" }
    $push = RunGit @("push", "origin", "HEAD:$Branch")
    if ($push.code -ne 0) { throw "post push failed: $($push.output)" }
    $state.post_sync_ok = $true

    $latestPath = Join-Path $CleanRepo "outputs\england_program_parcel_matrix_20260629\gas_emissions_updates\latest_changes.json"
    $latest = ReadJson $latestPath
    if ($latest) { $state.final_ready = [bool]$latest.final_ready; $state.verification_score_after = [string]$latest.verification_score_after; $state.browser_smoke_passed = [bool]$latest.browser_smoke_passed; $state.source_row_gate_passed = $latest.source_row_gate_passed }
  } finally {
    Pop-Location
  }
} catch {
  $state.error = $_.Exception.Message
  Say "AUTONOMOUS_RUNNER_ERROR=$($state.error)" Yellow
}

$state.completed_at = NowUtc
$stateFile = Join-Path $SourceStatusDir "aays_continue_runner_autonomous_state_20260704.json"
$state | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $stateFile -Encoding UTF8
$reportFile = Join-Path $SourceReportDir "aays_continue_runner_autonomous_report_20260704.txt"
@(
  "AAYS Gas Emissions Autonomous Continue Runner",
  "runner_installed=true",
  "runner_version=20260704_github_autonomous",
  "post_sync_ok=$($state.post_sync_ok)",
  "final_ready=$($state.final_ready)",
  "verification_score_after=$($state.verification_score_after)",
  "browser_smoke_passed=$($state.browser_smoke_passed)",
  "source_row_gate_passed=$($state.source_row_gate_passed)",
  "error=$($state.error)",
  "next_command=docs/chatgpt_status/gas_emissions/automation/aays_continue_runner_20260704.ps1"
) | Set-Content -LiteralPath $reportFile -Encoding UTF8

Get-Content -LiteralPath $reportFile
if ($state.post_sync_ok) { Say "PUSH_SYNC_OK=true" Green; Say "CONTINUE_RUNNER_READY=true" Green; exit 0 }
Say "CONTINUE_RUNNER_READY=false" Yellow
exit 3
