param(
  [string]$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1",
  [string]$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence",
  [string]$LogRoot = "C:\Users\cagda\Documents\GitHub\AAYS\_handoff_unpack\future_growth_contractor\logs",
  [switch]$SkipPipeline
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Say([string]$k, [object]$v) { Write-Host ($k + "=" + [string]$v) }
function Step([string]$s) { Write-Host ""; Write-Host ("=== " + $s + " ===") }
function Redact([string]$x) {
  if ($null -eq $x) { return "" }
  $r = [string]$x
  $r = [regex]::Replace($r, '(?i)(DATABASE_URL\s*=\s*)[^\s]+', '$1[REDACTED]')
  $r = [regex]::Replace($r, '(?i)(PGPASSWORD\s*=\s*)[^\s]+', '$1[REDACTED]')
  $r = [regex]::Replace($r, '(?i)(JWT_SECRET\s*=\s*)[^\s]+', '$1[REDACTED]')
  $r = [regex]::Replace($r, '(?i)((API_KEY|TOKEN)\s*=\s*)[^\s]+', '$1[REDACTED]')
  $r = [regex]::Replace($r, 'postgres(?:ql)?://[^\s''"]+', 'postgresql://[REDACTED]')
  $r = [regex]::Replace($r, 'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}', '[REDACTED_JWT]')
  return $r
}

Step "AAYS FGC watch or continue"
Say "mode" "same_powershell_no_new_window_secret_safe"
Say "bridge_root" $BridgeRoot
Say "repo_root" $RepoRoot

if (-not (Test-Path -LiteralPath $BridgeRoot)) { Say "status" "blocked"; Say "reason" "bridge_root_missing"; exit 2 }
if (-not (Test-Path -LiteralPath $RepoRoot)) { Say "status" "blocked"; Say "reason" "repo_root_missing"; exit 2 }

Step "Sync bridge"
Push-Location $BridgeRoot
try {
  git status --short 2>&1 | ForEach-Object { Write-Host (Redact ([string]$_)) }
  git pull --ff-only 2>&1 | ForEach-Object { Write-Host (Redact ([string]$_)) }
} catch {
  Write-Host (Redact $_.Exception.Message)
  Say "status" "blocked"
  Say "reason" "bridge_git_pull_failed"
  exit 2
} finally {
  Pop-Location
}

Step "Check running process"
$patterns = @("terrayield_fgc_local_continue.ps1", "AAYS_FGC_CONTINUE_LOCAL_SAFE.ps1", "contractor_load_to_postgres.py", "contractor_match_to_parcels.py", "contractor_export_for_app.py", "pytest future_growth")
$procs = @(Get-CimInstance Win32_Process | Where-Object {
  $cmd = [string]$_.CommandLine
  $hit = $false
  foreach ($p in $patterns) { if ($cmd -like ("*" + $p + "*")) { $hit = $true } }
  $hit
})

if ($procs.Count -gt 0) {
  Say "status" "running"
  Say "running_count" $procs.Count
  foreach ($p in $procs | Select-Object -First 8) {
    Say "pid" $p.ProcessId
    Say "process" (Redact ([string]$p.CommandLine))
  }
  if (Test-Path -LiteralPath $LogRoot) {
    $latest = Get-ChildItem -LiteralPath $LogRoot -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latest) {
      Say "latest_log" $latest.FullName
      Get-Content -LiteralPath $latest.FullName -Tail 80 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host (Redact ([string]$_)) }
    }
  }
  Say "decision" "do_not_start_duplicate"
  Say "next_wait_minutes" 10
  exit 0
}

Step "No running process; continue in same PowerShell"
$continueScript = Join-Path $BridgeRoot "ai-task-scripts\terrayield_fgc_local_continue.ps1"
if (-not (Test-Path -LiteralPath $continueScript)) {
  Say "status" "blocked"
  Say "reason" "continue_script_missing_after_pull"
  exit 2
}

if (-not (Test-Path -LiteralPath $LogRoot)) { New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null }
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$log = Join-Path $LogRoot ("fgc_continue_" + $stamp + ".log")
Say "status" "starting"
Say "log" $log

if ($SkipPipeline) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $continueScript -SkipPipeline 2>&1 | Tee-Object -FilePath $log | ForEach-Object { Write-Host (Redact ([string]$_)) }
} else {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $continueScript 2>&1 | Tee-Object -FilePath $log | ForEach-Object { Write-Host (Redact ([string]$_)) }
}
$exitCode = $LASTEXITCODE
Say "continue_exit_code" $exitCode
if ($exitCode -eq 0) {
  Say "status" "completed_or_no_duplicate"
  Say "next_action" "paste_last_80_log_lines_to_chatgpt_if_needed"
  exit 0
}
Say "status" "blocked_or_failed_closed"
Say "next_action" "paste_log_tail_to_chatgpt"
exit $exitCode
