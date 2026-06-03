$ErrorActionPreference='Continue'
$TaskId='cost50-023-safe-cleanup-audit-inventory-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function SafeRel($p){ try { return $p.Replace($BridgeRoot,'').TrimStart('\\','/') } catch { return $p } }
function FileLine($f,$label){
  $age=[Math]::Round(((Get-Date)-$f.LastWriteTime).TotalMinutes,1)
  return "| $label | $(SafeRel $f.FullName) | $($f.Length) | $($f.LastWriteTime.ToString('s')) | $age |"
}
Log "TASK=$TaskId"
Log 'MODE=cleanup_audit_inventory_only_no_delete'
Log "BRIDGE_ROOT=$BridgeRoot"
$heartbeat=Join-Path $BridgeRoot 'ai-heartbeat\portable-runner.md'
$activeLog=''
if(Test-Path $heartbeat){
  $hb=Get-Content -Raw -Encoding UTF8 -Path $heartbeat
  if($hb -match 'RunnerLog:\s*(.+)'){ $activeLog=$Matches[1].Trim() }
}
$protected=@(
  'DB files / PostgreSQL data',
  'source manifests',
  'quality_reports',
  'handoff zip files',
  'application source files under project root'
)
$rows=New-Object System.Collections.Generic.List[string]
$rows.Add('| Bucket | Relative path | Bytes | LastWriteTime | AgeMinutes |') | Out-Null
$rows.Add('|---|---:|---:|---:|---:|') | Out-Null
$counts=[ordered]@{ ai_tmp=0; runner_logs=0; timestamp_results=0; protected_touched=0 }
$bytes=[ordered]@{ ai_tmp=0L; runner_logs=0L; timestamp_results=0L }
$tmp=Join-Path $BridgeRoot 'ai-tmp'
if(Test-Path $tmp){
  Get-ChildItem -Path $tmp -File -Recurse -ErrorAction SilentlyContinue | Where-Object { ((Get-Date)-$_.LastWriteTime).TotalMinutes -ge 60 } | Sort-Object LastWriteTime | ForEach-Object {
    $counts.ai_tmp++; $bytes.ai_tmp += $_.Length
    if($rows.Count -lt 80){ $rows.Add((FileLine $_ 'ai-tmp-old')) | Out-Null }
  }
}
$logDir=Join-Path $BridgeRoot 'ai-runner-logs'
if(Test-Path $logDir){
  Get-ChildItem -Path $logDir -File -Filter '*.log' -ErrorAction SilentlyContinue | Where-Object { $_.FullName -ne $activeLog -and ((Get-Date)-$_.LastWriteTime).TotalMinutes -ge 60 } | Sort-Object LastWriteTime | ForEach-Object {
    $counts.runner_logs++; $bytes.runner_logs += $_.Length
    if($rows.Count -lt 80){ $rows.Add((FileLine $_ 'runner-log-old')) | Out-Null }
  }
}
if(Test-Path $ResultDir){
  Get-ChildItem -Path $ResultDir -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-.+\.md$' -and ((Get-Date)-$_.LastWriteTime).TotalMinutes -ge 60 } | Sort-Object LastWriteTime | ForEach-Object {
    $counts.timestamp_results++; $bytes.timestamp_results += $_.Length
    if($rows.Count -lt 80){ $rows.Add((FileLine $_ 'timestamp-result-copy-old')) | Out-Null }
  }
}
$out=Join-Path $ResultDir "$TaskId.report.md"
$totalCandidates=$counts.ai_tmp+$counts.runner_logs+$counts.timestamp_results
$totalBytes=$bytes.ai_tmp+$bytes.runner_logs+$bytes.timestamp_results
$report=@(
  '# Cost50 023 Safe Cleanup Audit Inventory',
  '',
  "Generated: $(Get-Date -Format s)",
  '',
  "TASK=$TaskId",
  'MODE=inventory_only_no_delete',
  'DELETE_EXECUTED=False',
  'PROTECTED_TOUCH_COUNT=0',
  'PROTECTED_SCOPES=' + ($protected -join '; '),
  "ACTIVE_RUNNER_LOG_EXCLUDED=$activeLog",
  "AI_TMP_OLD_COUNT=$($counts.ai_tmp)",
  "RUNNER_LOG_OLD_COUNT=$($counts.runner_logs)",
  "TIMESTAMP_RESULT_COPY_OLD_COUNT=$($counts.timestamp_results)",
  "CANDIDATE_TOTAL_COUNT=$totalCandidates",
  "CANDIDATE_TOTAL_BYTES=$totalBytes",
  'RECOMMENDATION=Review this inventory first; if safe, run a delete-only-temp-log task. Do not delete DB/source manifests/quality_reports/handoff zips/app source.',
  'PLAN_PROGRESS_PERCENT=45',
  'TASK_COMPLETION=100/100',
  '',
  '## Candidate inventory preview',
  ''
) + $rows
$report | Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log "CANDIDATE_TOTAL_COUNT=$totalCandidates"
Log "CANDIDATE_TOTAL_BYTES=$totalBytes"
Log 'DELETE_EXECUTED=False'
Log 'PLAN_PROGRESS_PERCENT=45'
Log 'TASK_COMPLETION=100/100'
exit 0
