param(
  [string]$RepoRoot = "F:\chatgpt\chat_gpt_clone_1_runner_clean",
  [string]$BridgeRoot = "F:\AAYS_GITHUB_BRIDGE_CLEAN2"
)
$ErrorActionPreference = "Stop"
$env:AAYS_REPO_ROOT = $RepoRoot
$env:AAYS_BRIDGE_ROOT = $BridgeRoot
Set-Location $RepoRoot
if (Test-Path ".git\index.lock") { Remove-Item ".git\index.lock" -Force }
git fetch origin main
git pull --rebase origin main
$QueueFile = Join-Path $RepoRoot "docs\chatgpt_status\aays1\queue\zzzz_115_security_batch_join_backoff.task.json"
$ScriptFile = Join-Path $RepoRoot "docs\chatgpt_status\security_public_safety\automation\115_security_batch_join_backoff.ps1"
if (-not (Test-Path $QueueFile)) { throw "Missing queue file: $QueueFile" }
if (-not (Test-Path $ScriptFile)) { throw "Missing automation file: $ScriptFile" }
& powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptFile
if ($LASTEXITCODE -ne 0) { throw "115 automation failed" }
$Out = Join-Path $RepoRoot "docs\chatgpt_status\security_public_safety\runner_outputs\115_security_batch_join_backoff.json"
if (-not (Test-Path $Out)) { throw "115 output missing: $Out" }
$Queue = Get-Content -LiteralPath $QueueFile -Raw | ConvertFrom-Json
$Queue.status = "done"
$Queue | Add-Member -NotePropertyName completed_at -NotePropertyValue (Get-Date).ToString("o") -Force
$Queue | Add-Member -NotePropertyName runner_status -NotePropertyValue "RUNNER_FINISHED_SINGLE_PASS" -Force
$Queue | Add-Member -NotePropertyName automation_exit_code -NotePropertyValue 0 -Force
$Queue | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $QueueFile -Encoding UTF8
git add "docs/chatgpt_status/aays1/queue/zzzz_115_security_batch_join_backoff.task.json" "docs/chatgpt_status/security_public_safety" "england_map_web/data/security_public_safety" "outputs/england_program_parcel_matrix_20260629/security_public_safety_updates"
$Changes = git status --porcelain
if ($Changes) {
  git commit -m "Run Security 115 batch join backoff"
  git fetch origin main
  git pull --rebase origin main
  git push origin main
}
Write-Host "SECURITY_115_DONE"
