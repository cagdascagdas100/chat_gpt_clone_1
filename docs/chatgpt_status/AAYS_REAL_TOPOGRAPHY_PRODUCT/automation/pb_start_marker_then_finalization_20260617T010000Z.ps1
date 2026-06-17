$ErrorActionPreference = 'Continue'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Branch = 'aays-runner-v17-icon-work-20260603-232706'
$Task = 'pb-start-marker-then-finalization-20260617T010000Z'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$ReportRel = "docs/chatgpt_status/$PageKey/reports/pb_start_marker_then_finalization_20260617T010000Z.txt"
$StatusRel = "docs/chatgpt_status/$PageKey/status/pb_start_marker_then_finalization_20260617T010000Z.txt"
$ReportPath = Join-Path $RepoRoot $ReportRel
$StatusPath = Join-Path $RepoRoot $StatusRel
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ReportPath),(Split-Path -Parent $StatusPath) | Out-Null
@("PAGE_KEY=$PageKey","TASK=$Task","STATUS=STARTED_MARKER_WRITTEN","REPORT_REPO_ROOT=$RepoRoot","FINAL_READY=false","NEXT=runtime finalization follows if runner can continue") | Out-File -FilePath $ReportPath -Encoding utf8
@("PAGE_KEY: $PageKey","TASK: $Task","STATUS: STARTED_MARKER_WRITTEN","REPORT_REPO_ROOT: $RepoRoot","FINAL_READY: false","REPORT: $ReportRel") | Out-File -FilePath $StatusPath -Encoding utf8
try {
  git -C $RepoRoot add $ReportRel $StatusRel | Out-Null
  $pending = git -C $RepoRoot status --porcelain -- $ReportRel $StatusRel
  if ($pending) {
    git -C $RepoRoot commit -m 'Mark planned buildings runner started' | Out-Null
    git -C $RepoRoot push origin HEAD:$Branch | Out-Null
  }
} catch { "MARKER_PUSH_ERROR=$($_.Exception.Message)" | Out-File -FilePath $ReportPath -Append -Encoding utf8 }
$FinalPath = Join-Path $RepoRoot "docs/chatgpt_status/$PageKey/automation/pb_runtime_finalization_single_runner_20260617T000000Z.ps1"
if (Test-Path -LiteralPath $FinalPath) { & $FinalPath } else { "FINAL_SCRIPT_MISSING=true" | Out-File -FilePath $ReportPath -Append -Encoding utf8 }
exit 0
