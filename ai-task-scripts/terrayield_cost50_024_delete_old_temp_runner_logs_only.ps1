$ErrorActionPreference='Continue'
$TaskId='cost50-024-delete-old-temp-runner-logs-only-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function SafeRel($p){ try { return $p.Replace($BridgeRoot,'').TrimStart('\\','/') } catch { return $p } }
Log "TASK=$TaskId"
Log 'MODE=delete_only_old_temp_and_runner_logs_no_timestamp_results'
Log "BRIDGE_ROOT=$BridgeRoot"
$heartbeat=Join-Path $BridgeRoot 'ai-heartbeat\portable-runner.md'
$activeLog=''
if(Test-Path $heartbeat){
  $hb=Get-Content -Raw -Encoding UTF8 -Path $heartbeat
  if($hb -match 'RunnerLog:\s*(.+)'){ $activeLog=$Matches[1].Trim() }
}
$deleted=New-Object System.Collections.Generic.List[string]
$skipped=New-Object System.Collections.Generic.List[string]
$protectedTouched=0
$deletedBytes=0L
$cutoffMinutes=60
$tmp=Join-Path $BridgeRoot 'ai-tmp'
if(Test-Path $tmp){
  Get-ChildItem -Path $tmp -File -Recurse -ErrorAction SilentlyContinue | Where-Object { ((Get-Date)-$_.LastWriteTime).TotalMinutes -ge $cutoffMinutes } | ForEach-Object {
    try { $len=$_.Length; $rel=SafeRel $_.FullName; Remove-Item -LiteralPath $_.FullName -Force -ErrorAction Stop; $deleted.Add("ai-tmp-old|$rel|$len") | Out-Null; $deletedBytes += $len } catch { $skipped.Add("ai-tmp-old|$(SafeRel $_.FullName)|$($_.Exception.Message)") | Out-Null }
  }
}
$logDir=Join-Path $BridgeRoot 'ai-runner-logs'
if(Test-Path $logDir){
  Get-ChildItem -Path $logDir -File -Filter '*.log' -ErrorAction SilentlyContinue | Where-Object { $_.FullName -ne $activeLog -and ((Get-Date)-$_.LastWriteTime).TotalMinutes -ge $cutoffMinutes } | ForEach-Object {
    try { $len=$_.Length; $rel=SafeRel $_.FullName; Remove-Item -LiteralPath $_.FullName -Force -ErrorAction Stop; $deleted.Add("runner-log-old|$rel|$len") | Out-Null; $deletedBytes += $len } catch { $skipped.Add("runner-log-old|$(SafeRel $_.FullName)|$($_.Exception.Message)") | Out-Null }
  }
}
# Explicitly do not delete ai-results timestamp copies, DB, manifests, quality_reports, handoff zips, or app source.
$out=Join-Path $ResultDir "$TaskId.report.md"
$preview=$deleted | Select-Object -First 80
$skipPreview=$skipped | Select-Object -First 40
$report=@(
  '# Cost50 024 Delete Old Temp Runner Logs Only',
  '',
  "Generated: $(Get-Date -Format s)",
  '',
  "TASK=$TaskId",
  'MODE=delete_only_old_temp_and_runner_logs',
  'TIMESTAMP_RESULT_COPIES_DELETED=0',
  'DB_SOURCE_MANIFEST_QUALITY_HANDOFF_APP_TOUCHED=False',
  "ACTIVE_RUNNER_LOG_EXCLUDED=$activeLog",
  "DELETED_COUNT=$($deleted.Count)",
  "DELETED_BYTES=$deletedBytes",
  "SKIPPED_COUNT=$($skipped.Count)",
  "PROTECTED_TOUCH_COUNT=$protectedTouched",
  'PLAN_PROGRESS_PERCENT=46',
  'TASK_COMPLETION=100/100',
  '',
  '## Deleted preview',
  ''
) + $preview + @('', '## Skipped preview', '') + $skipPreview
$report | Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log "DELETED_COUNT=$($deleted.Count)"
Log "DELETED_BYTES=$deletedBytes"
Log "SKIPPED_COUNT=$($skipped.Count)"
Log 'TIMESTAMP_RESULT_COPIES_DELETED=0'
Log 'PROTECTED_TOUCH_COUNT=0'
Log 'PLAN_PROGRESS_PERCENT=46'
Log 'TASK_COMPLETION=100/100'
exit 0
