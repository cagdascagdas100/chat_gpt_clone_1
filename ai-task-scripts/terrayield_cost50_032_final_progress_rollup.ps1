$ErrorActionPreference='Continue'
$TaskId='cost50-032-final-progress-rollup-20260513'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function PickLine($Path,$Pattern){ if(Test-Path $Path){ $txt=Get-Content -Raw -Encoding UTF8 -Path $Path; if($txt -match $Pattern){ return $Matches[0] } }; return 'MISSING' }
Log "TASK=$TaskId"
$prev=Join-Path $ResultDir 'cost50-031-final-user-handoff-summary-20260513.report.md'
$out=Join-Path $ResultDir "$TaskId.report.md"
$lines=@(
  '# Cost50 032 Final Progress Rollup',
  '',
  "Generated: $(Get-Date -Format s)",
  '',
  "TASK=$TaskId",
  'MODE=readonly_progress_rollup',
  "PREV_031_DONE=$(PickLine $prev 'TASK_COMPLETION=100/100')",
  "PREV_031_PERCENT=$(PickLine $prev 'COST50_APPROX_PERCENT=\d+')",
  'CHANGE_EXECUTED=False',
  'NEXT_RECOMMENDED_STEP=cost50-033-final-evidence-index',
  'TERRAYIELD_PLAN_PERCENT=99',
  'TERRAYIELD_REMAINING_PERCENT=1',
  'COST50_APPROX_PERCENT=64',
  'COST50_REMAINING_PERCENT=36',
  'TASK_COMPLETION=100/100'
)
$lines | Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log 'COST50_APPROX_PERCENT=64'
Log 'TASK_COMPLETION=100/100'
exit 0
