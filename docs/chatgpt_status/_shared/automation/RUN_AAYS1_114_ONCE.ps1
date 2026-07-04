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
$QueueFile = Join-Path $RepoRoot "docs\chatgpt_status\aays1\queue\zzzz_114_security_official_source_join_probe.task.json"
$ScriptFile = Join-Path $RepoRoot "docs\chatgpt_status\security_public_safety\automation\114_security_official_source_join_probe.ps1"
if (-not (Test-Path $QueueFile)) { throw "Missing queue file: $QueueFile" }
if (-not (Test-Path $ScriptFile)) { throw "Missing automation file: $ScriptFile" }
& powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptFile
if ($LASTEXITCODE -ne 0) { throw "114 automation failed" }
$Out = Join-Path $RepoRoot "docs\chatgpt_status\security_public_safety\runner_outputs\114_security_official_source_join_probe.json"
if (-not (Test-Path $Out)) { throw "114 output missing: $Out" }
$Queue = Get-Content -LiteralPath $QueueFile -Raw | ConvertFrom-Json
$Queue.status = "done"
$Queue | Add-Member -NotePropertyName completed_at -NotePropertyValue (Get-Date).ToString("o") -Force
$Queue | Add-Member -NotePropertyName runner_status -NotePropertyValue "RUNNER_FINISHED_SINGLE_PASS" -Force
$Queue | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $QueueFile -Encoding UTF8
git add "docs/chatgpt_status/aays1/queue/zzzz_114_security_official_source_join_probe.task.json" "docs/chatgpt_status/security_public_safety" "england_map_web/data/security_public_safety" "outputs/england_program_parcel_matrix_20260629/security_public_safety_updates"
$Changes = git status --porcelain
if ($Changes) {
  git commit -m "Run Security 114 official source join probe"
  git fetch origin main
  git pull --rebase origin main
  git push origin main
}
Write-Host "SECURITY_114_DONE"
