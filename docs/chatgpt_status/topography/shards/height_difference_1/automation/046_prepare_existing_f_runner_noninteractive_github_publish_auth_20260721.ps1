[CmdletBinding()]
param(
  [string]$RepoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707',
  [string]$Branch = 'codex/aays-single-runner-v5-20260706',
  [string]$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1',
  [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$TaskId = 'height-difference-1-official-boundary-elevation-samples-20260720'
$SlotId = 'height_difference_1'
$OutputRel = 'docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/027_noninteractive_publish_auth_preflight_latest.json'
$WebRel = 'england_map_web/data/aays_21_slots/height_difference_1/noninteractive_publish_auth_preflight_latest.json'

function Write-Json([string]$Path, [object]$Value) {
  $parent = Split-Path -Parent $Path
  if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 20), $utf8)
}

function Invoke-Captured([string]$File, [string[]]$Arguments, [string]$WorkingDirectory) {
  Push-Location -LiteralPath $WorkingDirectory
  $oldEap = $ErrorActionPreference
  try {
    $ErrorActionPreference = 'Continue'
    $lines = @(& $File @Arguments 2>&1)
    $code = $LASTEXITCODE
    $text = (($lines | Out-String).Trim())
    return [pscustomobject]@{ exit_code = $code; stdout = $text; stderr = $text }
  } finally {
    $ErrorActionPreference = $oldEap
    Pop-Location
  }
}

function Redact([string]$Text) {
  return (($Text -replace '(?i)(token|password|authorization)[:=]\S+','$1=REDACTED') -replace 'https://[^\s@]+@github\.com','https://REDACTED@github.com')
}

$blockers = New-Object System.Collections.Generic.List[string]
$facts = [ordered]@{}
$git = Get-Command git -ErrorAction SilentlyContinue
$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $git) { [void]$blockers.Add('GIT_EXECUTABLE_NOT_FOUND') }
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { [void]$blockers.Add('CANONICAL_REPO_ROOT_NOT_FOUND') }

$oldPrompt = $env:GIT_TERMINAL_PROMPT
$env:GIT_TERMINAL_PROMPT = '0'
try {
  $alreadyReady = $false
  if ($git -and (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
    $origin = Invoke-Captured $git.Source @('-C',$RepoRoot,'remote','get-url','origin') $RepoRoot
    $facts.origin_exit_code = $origin.exit_code
    $facts.origin_url_redacted = if ($origin.stdout -match 'github\.com[:/]([^/]+/[^/.]+)') { 'github.com/' + $Matches[1] } else { 'UNRESOLVED' }
    if ($origin.exit_code -ne 0) { [void]$blockers.Add('ORIGIN_REMOTE_NOT_READABLE') }
    elseif ($origin.stdout -notmatch [regex]::Escape($RepoFullName)) { [void]$blockers.Add('ORIGIN_REPOSITORY_MISMATCH') }

    if ($blockers.Count -eq 0) {
      $before = Invoke-Captured $git.Source @('-C',$RepoRoot,'ls-remote','--exit-code','origin',('refs/heads/' + $Branch)) $RepoRoot
      $facts.git_ls_remote_before_exit_code = $before.exit_code
      $facts.git_ls_remote_before_ok = ($before.exit_code -eq 0)
      $alreadyReady = [bool]$facts.git_ls_remote_before_ok
      if (-not $alreadyReady) { $facts.git_ls_remote_before_error = Redact $before.stderr }
    }
  }

  if (-not $alreadyReady -and $blockers.Count -eq 0) {
    if (-not $gh) {
      [void]$blockers.Add('GITHUB_CLI_NOT_FOUND_FOR_AUTH_RECOVERY')
    } else {
      $ghStatus = Invoke-Captured $gh.Source @('auth','status','--active','--hostname','github.com') $RepoRoot
      $facts.gh_auth_status_exit_code = $ghStatus.exit_code
      $facts.gh_authenticated = ($ghStatus.exit_code -eq 0)
      $facts.gh_auth_status_summary = Redact (($ghStatus.stdout + ' ' + $ghStatus.stderr).Trim())
      if ($ghStatus.exit_code -ne 0) { [void]$blockers.Add('GH_AUTH_NOT_ACTIVE_FOR_GITHUB_COM') }
    }
  }

  if (-not $Apply) {
    $status = if ($blockers.Count -gt 0) { 'BLOCKED_NONINTERACTIVE_PUBLISH_AUTH_PREFLIGHT' } elseif ($alreadyReady) { 'GIT_ALREADY_NONINTERACTIVE_AUTHENTICATED' } else { 'READY_FOR_GH_SETUP_GIT_APPLY' }
  } else {
    if ($blockers.Count -gt 0) {
      $status = 'BLOCKED_NONINTERACTIVE_PUBLISH_AUTH_APPLY'
    } elseif ($alreadyReady) {
      $status = 'GIT_ALREADY_NONINTERACTIVE_AUTHENTICATED'
    } else {
      $setup = Invoke-Captured $gh.Source @('auth','setup-git','--hostname','github.com') $RepoRoot
      $facts.gh_auth_setup_git_exit_code = $setup.exit_code
      if ($setup.exit_code -ne 0) {
        [void]$blockers.Add('GH_AUTH_SETUP_GIT_FAILED')
        $facts.gh_auth_setup_git_error = Redact (($setup.stderr + ' ' + $setup.stdout).Trim())
        $status = 'BLOCKED_NONINTERACTIVE_PUBLISH_AUTH_APPLY'
      } else {
        $after = Invoke-Captured $git.Source @('-C',$RepoRoot,'ls-remote','--exit-code','origin',('refs/heads/' + $Branch)) $RepoRoot
        $facts.git_ls_remote_after_exit_code = $after.exit_code
        $facts.git_ls_remote_after_ok = ($after.exit_code -eq 0)
        if ($after.exit_code -ne 0) {
          [void]$blockers.Add('NONINTERACTIVE_GIT_LS_REMOTE_STILL_FAILED_AFTER_GH_SETUP')
          $facts.git_ls_remote_after_error = Redact $after.stderr
          $status = 'BLOCKED_NONINTERACTIVE_PUBLISH_AUTH_APPLY'
        } else {
          $status = 'NONINTERACTIVE_GITHUB_PUBLISH_AUTH_READY'
        }
      }
    }
  }
} finally {
  $env:GIT_TERMINAL_PROMPT = $oldPrompt
}

$result = [ordered]@{
  schema_version = 2
  slot_id = $SlotId
  task_id = $TaskId
  branch = $Branch
  status = $status
  apply_requested = [bool]$Apply
  blockers = @($blockers)
  facts = $facts
  existing_git_auth_accepted_without_gh = $true
  gh_used_only_as_fallback = $true
  token_or_secret_output_forbidden = $true
  windows_powershell_5_1_compatible = $true
  starts_runner = $false
  stops_runner = $false
  creates_runner = $false
  pushes_results = $false
  next_step = if ($status -eq 'NONINTERACTIVE_GITHUB_PUBLISH_AUTH_READY' -or $status -eq 'GIT_ALREADY_NONINTERACTIVE_AUTHENTICATED') { 'RERUN_EXISTING_SINGLE_RUNNER_FOR_EXACT_REVISION_14_THEN_VERIFY_REMOTE_OUTPUT' } else { 'RESOLVE_REPORTED_AUTH_BLOCKER_WITHOUT_CREATING_A_NEW_RUNNER' }
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}

foreach ($relative in @($OutputRel,$WebRel)) { Write-Json (Join-Path $RepoRoot ($relative -replace '/','\')) $result }
$result | ConvertTo-Json -Depth 20
if ($status -like 'BLOCKED*') { exit 2 }
exit 0
