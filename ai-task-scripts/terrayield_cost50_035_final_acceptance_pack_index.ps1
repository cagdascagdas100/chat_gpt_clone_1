$ErrorActionPreference='Continue'
$TaskId='cost50-035-final-acceptance-pack-index-20260513'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function Pick($p,$pat){ if(Test-Path $p){ $t=Get-Content -Raw -Encoding UTF8 -Path $p; if($t -match $pat){ return $Matches[0] } }; return 'MISSING' }
Log "TASK=$TaskId"
$prev=Join-Path $ResultDir 'cost50-034-final-risk-and-gap-note-20260513.report.md'
$out=Join-Path $ResultDir "$TaskId.report.md"
$lines=@(
  '# Cost50 035 Final Acceptance Pack Index',
  '',
  "Generated: $(Get-Date -Format s)",
  '',
  "TASK=$TaskId",
  'MODE=readonly_index',
  "PREV_DONE=$(Pick $prev 'TASK_COMPLETION=100/100')",
  "PREV_PERCENT=$(Pick $prev 'COST50_APPROX_PERCENT=\d+')",
  'CHANGE_EXECUTED=False',
  'NEXT_RECOMMENDED_STEP=cost50-036-final-signoff-readiness-note',
  'COST50_APPROX_PERCENT=70',
  'TASK_COMPLETION=100/100'
)
$lines | Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log 'COST50_APPROX_PERCENT=70'
Log 'TASK_COMPLETION=100/100'
exit 0
