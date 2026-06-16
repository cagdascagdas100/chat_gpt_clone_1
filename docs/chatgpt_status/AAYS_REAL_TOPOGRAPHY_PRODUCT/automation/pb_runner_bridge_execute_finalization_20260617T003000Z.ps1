$ErrorActionPreference = 'Continue'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Branch = 'aays-runner-v17-icon-work-20260603-232706'
$Task = 'pb-runner-bridge-execute-finalization-20260617T003000Z'
$Worktree = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706'
$RepoRoot = if (Test-Path -LiteralPath $Worktree) { $Worktree } else { (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path }
$FinalScriptRel = "docs/chatgpt_status/$PageKey/automation/pb_runtime_finalization_single_runner_20260617T000000Z.ps1"
$FinalReportRel = "docs/chatgpt_status/$PageKey/reports/pb_runtime_finalization_single_runner_20260617T000000Z.txt"
$FinalStatusRel = "docs/chatgpt_status/$PageKey/status/pb_runtime_finalization_single_runner_20260617T000000Z.txt"
$BridgeReportRel = "docs/chatgpt_status/$PageKey/reports/pb_runner_bridge_execute_finalization_20260617T003000Z.txt"
$BridgeStatusRel = "docs/chatgpt_status/$PageKey/status/pb_runner_bridge_execute_finalization_20260617T003000Z.txt"
$FinalScriptPath = Join-Path $RepoRoot $FinalScriptRel
$FinalReportPath = Join-Path $RepoRoot $FinalReportRel
$BridgeReportPath = Join-Path $RepoRoot $BridgeReportRel
$BridgeStatusPath = Join-Path $RepoRoot $BridgeStatusRel
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BridgeReportPath),(Split-Path -Parent $BridgeStatusPath) | Out-Null
$scriptExists = Test-Path -LiteralPath $FinalScriptPath
$exitCodeValue = 'not_run'
if ($scriptExists) {
  try {
    & $FinalScriptPath
    $exitCodeValue = $LASTEXITCODE
  } catch {
    $exitCodeValue = 'exception'
  }
}
$finalReportExists = Test-Path -LiteralPath $FinalReportPath
@(
'LAYER=Nearby Planned Developments',
"PAGE_KEY=$PageKey",
"TASK=$Task",
"BRANCH=$Branch",
'RUNNER_SEEN=true',
"WORKTREE=$RepoRoot",
"FINAL_SCRIPT_EXISTS=$($scriptExists.ToString().ToLower())",
"FINALIZATION_EXIT_CODE=$exitCodeValue",
"FINALIZATION_REPORT_EXISTS=$($finalReportExists.ToString().ToLower())",
"FINALIZATION_REPORT=$FinalReportRel",
"FINAL_STATUS=$(if ($finalReportExists) { 'FINALIZATION_OUTPUT_AVAILABLE' } else { 'FINALIZATION_OUTPUT_STILL_MISSING' })",
'FINAL_READY=false'
) | Out-File -FilePath $BridgeReportPath -Encoding utf8
@(
"PAGE_KEY: $PageKey",
"TASK: $Task",
"STATUS: $(if ($finalReportExists) { 'FINALIZATION_OUTPUT_AVAILABLE' } else { 'FINALIZATION_OUTPUT_STILL_MISSING' })",
"FINALIZATION_REPORT_EXISTS: $($finalReportExists.ToString().ToLower())",
'FINAL_READY: false',
"REPORT: $BridgeReportRel"
) | Out-File -FilePath $BridgeStatusPath -Encoding utf8
try {
  Push-Location $RepoRoot
  git add $BridgeReportRel $BridgeStatusRel $FinalReportRel $FinalStatusRel 2>$null
  git commit -m "AAYS PB runner bridge finalization report" 2>$null
  git push origin $Branch 2>$null
  Pop-Location
} catch {}
exit 0
