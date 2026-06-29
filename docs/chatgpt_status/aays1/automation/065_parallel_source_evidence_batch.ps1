$ErrorActionPreference = "Stop"

$RepoRoot = "F:\chatgpt\chat_gpt_clone_1_main"
$BridgeRoot = "F:\AAYS_GITHUB_BRIDGE_CLEAN2"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StatusDir = Join-Path $RepoRoot "docs\chatgpt_status\aays1\status"
$ReportDir = Join-Path $RepoRoot "docs\chatgpt_status\aays1\reports"
New-Item -ItemType Directory -Force -Path $StatusDir,$ReportDir | Out-Null

$status = "status=BLOCKED_SCRIPT_CREATION_REQUIRES_SOURCE_FETCH_IMPLEMENTATION`nfinal_ready=false`nblocker=parallel_source_fetch_script_was_not_committed_by_chatgpt_connector`nupdated_at=$Stamp"
$status | Set-Content -Encoding UTF8 (Join-Path $StatusDir "065_parallel_source_evidence_batch_blocked_$Stamp.txt")
"# 065 Parallel Source Evidence Batch Blocked`n`nThe runner model is installed and working. The next acceleration step is source/evidence fetch in a parallel batch. No fake evidence, no fake polygon, no DB write." | Set-Content -Encoding UTF8 (Join-Path $ReportDir "065_parallel_source_evidence_batch_blocked_$Stamp.md")

Set-Location $RepoRoot
git add -- "docs/chatgpt_status/aays1/status" "docs/chatgpt_status/aays1/reports"
git commit -m "Report blocked parallel evidence batch implementation"
git pull --rebase origin main
git push origin HEAD:main
exit 0
