param(
  [string]$ZipPath = "C:\Users\cagda\Downloads\AAYS_TerraYield_FutureGrowth_Contractor_Handoff.zip",
  [string]$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence",
  [string]$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1",
  [string]$UnpackRoot = "C:\Users\cagda\Documents\GitHub\AAYS\_handoff_unpack\future_growth_contractor",
  [switch]$SkipPipeline
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Say([string]$k, [object]$v) { Write-Host ($k + "=" + [string]$v) }
function Step([string]$s) { Write-Host ""; Write-Host ("=== " + $s + " ===") }
function FailClosed([string]$reason) { Say "pipeline_stop" "fail_closed"; Say "blocked_reason" $reason; exit 2 }
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
function RunChecked([string]$label, [scriptblock]$cmd) {
  Step $label
  $global:LASTEXITCODE = 0
  & $cmd 2>&1 | ForEach-Object { Write-Host (Redact ([string]$_)) }
  if ($LASTEXITCODE -ne 0) { FailClosed ($label + "_exit_" + $LASTEXITCODE) }
}
function ReadJsonSafe([string]$path) {
  try { return (Get-Content -LiteralPath $path -Raw | ConvertFrom-Json) } catch { return $null }
}

Step "AAYS TerraYield FGC local continue"
Say "mode" "secret_safe_fail_closed"
Say "repo_root" $RepoRoot
Say "bridge_root" $BridgeRoot
Say "zip_path" $ZipPath
if (-not (Test-Path -LiteralPath $RepoRoot)) { FailClosed "repo_root_missing" }
if (-not (Test-Path -LiteralPath $BridgeRoot)) { FailClosed "bridge_root_missing" }
if (-not (Test-Path -LiteralPath $ZipPath)) { FailClosed "handoff_zip_missing" }

Step "Unpack handoff"
if (Test-Path -LiteralPath $UnpackRoot) { Remove-Item -LiteralPath $UnpackRoot -Recurse -Force }
New-Item -ItemType Directory -Path $UnpackRoot -Force | Out-Null
Expand-Archive -LiteralPath $ZipPath -DestinationPath $UnpackRoot -Force
$root = $UnpackRoot
$children = @(Get-ChildItem -LiteralPath $UnpackRoot -Directory)
if ($children.Count -eq 1 -and (Test-Path -LiteralPath (Join-Path $children[0].FullName "manifest"))) { $root = $children[0].FullName }
Say "handoff_root" $root
foreach ($d in @("docs","future_growth_stage_artifacts","contractor_db","runner","audit_results_sanitized","manifest")) {
  $p = Join-Path $root $d
  Say ("handoff_" + $d + "_present") (Test-Path -LiteralPath $p)
  if (-not (Test-Path -LiteralPath $p)) { FailClosed ("handoff_missing_" + $d) }
}

Step "Repo file match"
Push-Location $RepoRoot
try {
  RunChecked "git status short" { git status --short }
  $needed = @("scripts\contractor_env.py", "scripts\contractor_load_to_postgres.py", "scripts\contractor_match_to_parcels.py", "scripts\contractor_export_for_app.py")
  foreach ($f in $needed) { Say ("repo_file_" + $f.Replace('\\','_') + "_present") (Test-Path -LiteralPath $f); if (-not (Test-Path -LiteralPath $f)) { FailClosed ("missing_repo_file_" + $f) } }
  Say "db_transfer_present" (Test-Path -LiteralPath "db_transfer")
  if (-not (Test-Path -LiteralPath "db_transfer")) { FailClosed "missing_db_transfer" }

  RunChecked "py_compile contractor scripts" { python -m py_compile scripts\contractor_env.py scripts\contractor_load_to_postgres.py scripts\contractor_match_to_parcels.py scripts\contractor_export_for_app.py }

  $preflight = Join-Path $BridgeRoot "ai-task-scripts\terrayield_079_contractor_db_env_loader_preflight.ps1"
  if (-not (Test-Path -LiteralPath $preflight)) { FailClosed "missing_preflight_script_in_bridge" }
  RunChecked "contractor db env loader preflight" { powershell -NoProfile -ExecutionPolicy Bypass -File $preflight }

  $auditCandidates = @()
  $auditCandidates += Get-ChildItem -LiteralPath $root -Recurse -Filter "*.json" -ErrorAction SilentlyContinue
  $auditCandidates += Get-ChildItem -LiteralPath $RepoRoot -Recurse -Filter "*preflight*.json" -ErrorAction SilentlyContinue
  $preflightOk = $false
  foreach ($j in ($auditCandidates | Sort-Object LastWriteTime -Descending | Select-Object -First 20)) {
    $o = ReadJsonSafe $j.FullName
    if ($null -ne $o) {
      $status = [string]$o.status
      $creds = [string]$o.db_credentials_present
      $conn = [string]$o.connection_ok
      $query = [string]$o.db_query_ok
      if ($status -eq "completed" -and $creds -eq "True" -and $conn -eq "True" -and $query -eq "True") { $preflightOk = $true; Say "preflight_artifact" $j.FullName; break }
    }
  }
  Say "preflight_required_status" "completed/true/true/true"
  Say "preflight_ok" $preflightOk
  if (-not $preflightOk) { FailClosed "preflight_artifact_not_confirmed_completed_true_true_true" }

  if (-not (Test-Path -LiteralPath "future_growth\tests")) { FailClosed "missing_future_growth_tests" }
  RunChecked "future growth pytest" { python -m pytest future_growth\tests -q }

  Step "Secret risk scan"
  $diff1 = git diff --cached 2>$null
  $diff2 = git diff 2>$null
  $combined = (($diff1 + $diff2) -join "`n")
  $risk = $combined -match '(?i)(DATABASE_URL\s*=|PGPASSWORD\s*=|JWT_SECRET\s*=|API_KEY\s*=|TOKEN\s*=|postgres(?:ql)?://|eyJ[A-Za-z0-9_-]{10,}\.)'
  Say "secret_risk_detected" $risk
  if ($risk) { Say "secret_risk_note" "[REDACTED] pattern found in git diff; inspect locally before commit"; FailClosed "secret_risk_detected" }

  if ($SkipPipeline) { Say "pipeline_skipped" $true; exit 0 }

  Step "Contractor pipeline"
  $schemaCandidates = @("scripts\contractor_apply_schema.py", "db_transfer\apply_contractor_schema.py", "scripts\contractor_schema_apply.py")
  $schema = $schemaCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  if (-not $schema) { FailClosed "missing_schema_apply_script" }
  RunChecked "schema apply" { python $schema }
  RunChecked "contractor DB load" { python scripts\contractor_load_to_postgres.py }
  RunChecked "parcel match" { python scripts\contractor_match_to_parcels.py }
  RunChecked "app export" { python scripts\contractor_export_for_app.py }
  if (Test-Path -LiteralPath "scripts\contractor_final_audit.py") { RunChecked "final audit" { python scripts\contractor_final_audit.py } } else { Say "final_audit" "script_not_found_git_diff_scan_used" }

  Say "integration_status" "completed_or_pipeline_scripts_returned_success"
  Say "future_growth_positioning" "Kesin fiyat tahmini degildir"
  Say "next_action" "son_log_ozetini_chatgpt_ile_paylas"
  exit 0
} finally {
  Pop-Location
}
