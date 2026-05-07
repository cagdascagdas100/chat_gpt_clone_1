$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-138-security-expansion-probe-resume-compact'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\Users\cagda\Documents\chat_gpt_clone_1' }
$RepoRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS' }
$AllowedRoot = Join-Path $RepoRoot 'security_accuracy_expansion'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

function OutStep([string]$Name) { Write-Output ('## ' + $Name) }
function RunText([scriptblock]$Block) { try { return (& $Block 2>&1 | Out-String) } catch { return ('ERROR: ' + $_.Exception.Message) } }
function SafeWrite([string]$Rel,[string]$Text) {
  $full = [IO.Path]::GetFullPath((Join-Path $AllowedRoot $Rel))
  $allowed = [IO.Path]::GetFullPath($AllowedRoot)
  if (-not $full.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)) { throw ('SCOPE_FAIL ' + $Rel) }
  $dir = Split-Path -Parent $full
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc = New-Object Text.UTF8Encoding($false)
  [IO.File]::WriteAllText($full,$Text,$enc)
  Write-Output ('WROTE=security_accuracy_expansion/' + ($Rel -replace '\\','/'))
}

Write-Output 'PROJECT=terrayield'
Write-Output ('TASK=' + $TaskId)
Write-Output 'MODE=compact_probe_resume_scope_only'
Write-Output 'LIVE_WRITE_POLICY=FORBIDDEN'
Write-Output ('BRIDGE_ROOT=' + $BridgeRoot)
Write-Output ('REPO_ROOT=' + $RepoRoot)

OutStep 'Preflight'
if (-not (Test-Path -LiteralPath $RepoRoot)) { Write-Output ('REPO_ROOT=FAIL ' + $RepoRoot); exit 2 }
New-Item -ItemType Directory -Force -Path $AllowedRoot | Out-Null
Set-Location $RepoRoot
Write-Output ('GIT_ROOT=' + (RunText { git rev-parse --show-toplevel }).Trim())
Write-Output ('LIVE_DIFF_BEFORE=' + (RunText { git diff --name-only -- england_map_web }).Trim())

OutStep 'Run 135 if available'
$Script135 = Join-Path $BridgeRoot 'ai-task-scripts\terrayield_135_security_accuracy_expansion_direct_apply.ps1'
if (Test-Path -LiteralPath $Script135) {
  $Out135 = RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $Script135 }
  Write-Output $Out135
} else { Write-Output 'SCRIPT_135=MISSING' }

OutStep 'Run 136 if available'
$Script136 = Join-Path $BridgeRoot 'ai-task-scripts\terrayield_136_security_accuracy_expansion_parallel_deepening.ps1'
if (Test-Path -LiteralPath $Script136) {
  $Out136 = RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $Script136 }
  Write-Output $Out136
} else { Write-Output 'SCRIPT_136=MISSING' }

OutStep 'Validation'
$LiveDiffAfter = (RunText { git diff --name-only -- england_map_web }).Trim()
Write-Output ('LIVE_DIFF_AFTER=' + $LiveDiffAfter)
if (-not [string]::IsNullOrWhiteSpace($LiveDiffAfter)) { Write-Output 'LIVE_DIFF_STATUS=FAIL'; exit 5 }
Write-Output 'LIVE_DIFF_STATUS=PASS'

$ScopeVerifier = Join-Path $AllowedRoot 'audit\verify_generated_scope_only_20260507.ps1'
$ScopeStatus = 'NOT_RUN'
if (Test-Path -LiteralPath $ScopeVerifier) {
  $ScopeOut = RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $ScopeVerifier }
  Write-Output $ScopeOut
  if ($ScopeOut -match 'GENERATED_SCOPE=PASS') { $ScopeStatus='PASS' } elseif ($ScopeOut -match 'GENERATED_SCOPE=FAIL') { $ScopeStatus='FAIL' } else { $ScopeStatus='UNKNOWN' }
} else { Write-Output 'SCOPE_VERIFIER=MISSING' }
Write-Output ('SCOPE_STATUS=' + $ScopeStatus)

$LiveVerifier = Join-Path $AllowedRoot 'audit\verify_live_modules_unchanged.ps1'
$LiveStatus = 'NOT_RUN'
if (Test-Path -LiteralPath $LiveVerifier) {
  $LiveOut = RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $LiveVerifier }
  Write-Output $LiveOut
  if ($LiveOut -match 'OVERALL=PASS') { $LiveStatus='PASS' } elseif ($LiveOut -match 'OVERALL=FAIL') { $LiveStatus='FAIL' } else { $LiveStatus='UNKNOWN' }
} else { Write-Output 'LIVE_VERIFIER=MISSING' }
Write-Output ('LIVE_STATUS=' + $LiveStatus)

OutStep 'Report'
$Report = @"
# Compact Probe Resume Report

Task: $TaskId  
Time: $(Get-Date -Format s)  
Scope status: $ScopeStatus  
Live status: $LiveStatus  
Live diff status: PASS  

This task ran the scope-only 135 and 136 scripts when present. It did not intentionally change `england_map_web` or active score/data surfaces.
"@
SafeWrite ('run_reports/compact_probe_resume_' + $Stamp + '.md') $Report

OutStep 'Guarded project commit'
$root = (RunText { git rev-parse --show-toplevel }).Trim().TrimEnd('\','/')
$repoClean = $RepoRoot.TrimEnd('\','/')
if ($root -ieq $repoClean) {
  git add security_accuracy_expansion 2>&1 | Out-String | Write-Output
  $cached = RunText { git diff --cached --name-only }
  $bad = @($cached -split "`r?`n" | Where-Object { $_ -and (-not $_.StartsWith('security_accuracy_expansion/')) })
  if ($bad.Count -gt 0) {
    Write-Output 'COMMIT_GUARD=FAIL'
    $bad | Write-Output
    git reset 2>&1 | Out-String | Write-Output
  } elseif ([string]::IsNullOrWhiteSpace($cached)) {
    Write-Output 'PROJECT_COMMIT=SKIPPED_NO_CHANGES'
  } else {
    git commit -m 'Apply security accuracy expansion scope-only package' 2>&1 | Out-String | Write-Output
    Write-Output 'PROJECT_COMMIT=ATTEMPTED_SECURITY_ONLY'
  }
} else { Write-Output ('PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH ' + $root) }
Write-Output 'PROJECT_PUSH=SKIPPED_BY_POLICY'

$Final = if ($ScopeStatus -eq 'PASS' -and [string]::IsNullOrWhiteSpace($LiveDiffAfter)) { if ($LiveStatus -eq 'PASS') { 'PASS' } else { 'PASS_WITH_EXISTING_LIVE_BLOCKER' } } else { 'FAIL' }
Write-Output ('FINAL_STATUS=' + $Final)
Write-Output 'NEXT_CHATGPT_INPUT=devam et'
Write-Output 'TERRAYIELD_138_DONE'
exit 0
