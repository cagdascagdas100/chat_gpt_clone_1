$ErrorActionPreference = 'Continue'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Branch = 'aays-runner-v17-icon-work-20260603-232706'
$Task = 'pb-runner-visibility-probe-20260617T001500Z'
$Worktree = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706'
$RepoRoot = if (Test-Path -LiteralPath $Worktree) { $Worktree } else { (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path }
$ReportRel = "docs/chatgpt_status/$PageKey/reports/pb_runner_visibility_probe_20260617T001500Z.txt"
$StatusRel = "docs/chatgpt_status/$PageKey/status/pb_runner_visibility_probe_20260617T001500Z.txt"
$ReportPath = Join-Path $RepoRoot $ReportRel
$StatusPath = Join-Path $RepoRoot $StatusRel
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ReportPath),(Split-Path -Parent $StatusPath) | Out-Null
@(
'LAYER=Nearby Planned Developments',
"PAGE_KEY=$PageKey",
"TASK=$Task",
"BRANCH=$Branch",
'RUNNER_SEEN=true',
"WORKTREE_EXISTS=$((Test-Path -LiteralPath $Worktree).ToString().ToLower())",
"FINALIZATION_REPORT_EXPECTED=docs/chatgpt_status/$PageKey/reports/pb_runtime_finalization_single_runner_20260617T000000Z.txt",
"FINAL_STATUS=RUNNER_VISIBLE_NEEDS_FINALIZATION_EXECUTION",
'FINAL_READY: false'
) | Out-File -FilePath $ReportPath -Encoding utf8
@(
"PAGE_KEY: $PageKey",
"TASK: $Task",
'STATUS: RUNNER_VISIBLE_NEEDS_FINALIZATION_EXECUTION',
'FINAL_READY: false',
"REPORT: $ReportRel"
) | Out-File -FilePath $StatusPath -Encoding utf8
exit 0
