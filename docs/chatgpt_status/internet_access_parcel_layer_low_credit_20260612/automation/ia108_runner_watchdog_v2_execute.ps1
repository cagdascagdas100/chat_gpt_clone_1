$ErrorActionPreference = "Continue"

$pageKey = "internet_access_parcel_layer_low_credit_20260612"
$taskId = "internet-access-108-real-parcel-final-gate"
$fixId = "ia108-runner-watchdog-v2-execute"
$pageDir = "docs/chatgpt_status/$pageKey"
$statusDir = "$pageDir/status"
$reportsDir = "$pageDir/reports"
$heartbeatDir = "$pageDir/heartbeat"
$runnerOutDir = "$pageDir/runner_outputs"
$globalReport = "docs/chatgpt_status/reports/$taskId.json"
$v2Script = "$pageDir/automation/ia108_real_geometry_join_v2_schema_probe.ps1"
$v2Report = "$reportsDir/ia108_real_geometry_join_v2_schema_probe_report.json"
$watchdogReport = "$reportsDir/ia108_runner_watchdog_v2_execute_report.json"
$watchdogStatus = "$statusDir/ia108_runner_watchdog_v2_execute.status"
$watchdogLog = "$statusDir/ia108_runner_watchdog_v2_execute.log"

New-Item -ItemType Directory -Force $statusDir,$reportsDir,$heartbeatDir,$runnerOutDir,"docs/chatgpt_status/reports" | Out-Null
"WATCHDOG_STARTED=$(Get-Date -Format o)" | Set-Content -Encoding UTF8 "$heartbeatDir/latest.txt"

$result = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  fix_id = $fixId
  status = "WATCHDOG_STARTED"
  v2_script = $v2Script
  v2_report = $v2Report
  global_report = $globalReport
  started_at = (Get-Date -Format o)
}

try {
  if (!(Test-Path $v2Script)) {
    $result.status = "BLOCKED_V2_SCRIPT_MISSING"
    $result.completion_percent = 79
    $result.final_ready = $false
    $result.production_complete = $false
    $result.reason = "v2 automation script missing"
  } else {
    if (!(Test-Path $v2Report)) {
      "RUNNING_V2_SCRIPT=$v2Script" | Add-Content -Encoding UTF8 $watchdogLog
      powershell -NoProfile -ExecutionPolicy Bypass -File $v2Script *>&1 | Tee-Object -FilePath $watchdogLog -Append
      $result.v2_exit_code = $LASTEXITCODE
    } else {
      $result.v2_exit_code = 0
      $result.note = "v2 report already existed before watchdog execution"
    }

    $result.v2_report_exists = Test-Path $v2Report
    $result.global_report_exists = Test-Path $globalReport

    if (Test-Path $v2Report) {
      try {
        $v2 = Get-Content $v2Report -Raw | ConvertFrom-Json
        $result.v2_status = $v2.status
        $result.v2_completion_percent = $v2.completion_percent
        $result.joined_geometry_count = $v2.joined_geometry_count
        $result.null_geometry_after_join = $v2.null_geometry_after_join
      } catch {
        $result.v2_report_parse_error = $_.Exception.Message
      }
    }

    if (Test-Path $globalReport) {
      try {
        $g = Get-Content $globalReport -Raw | ConvertFrom-Json
        $result.final_status = $g.FINAL_STATUS
        $result.product_progress_estimate = $g.PRODUCT_PROGRESS_ESTIMATE
        $result.production_complete = $g.PRODUCTION_COMPLETE
      } catch {
        $result.global_report_parse_error = $_.Exception.Message
      }
    }

    if ($result.final_status -eq "FINAL_READY_CONFIRMED" -and $result.product_progress_estimate -eq 100 -and $result.production_complete -eq $true) {
      $result.status = "FINAL_READY_CONFIRMED"
      $result.completion_percent = 100
      $result.final_ready = $true
    } elseif ($result.v2_report_exists) {
      $result.status = "V2_EXECUTED_FINAL_NOT_READY"
      $result.completion_percent = 80
      $result.final_ready = $false
    } else {
      $result.status = "V2_EXECUTION_DID_NOT_PRODUCE_REPORT"
      $result.completion_percent = 79
      $result.final_ready = $false
    }
  }
} catch {
  $result.status = "WATCHDOG_SCRIPT_ERROR"
  $result.completion_percent = 79
  $result.final_ready = $false
  $result.production_complete = $false
  $result.error = $_.Exception.Message
}

$result.finished_at = (Get-Date -Format o)
$result | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $watchdogReport
"status=$($result.status)`ncompletion_percent=$($result.completion_percent)`nv2_report_exists=$($result.v2_report_exists)`nfinal_status=$($result.final_status)`nreport=$watchdogReport" | Set-Content -Encoding UTF8 $watchdogStatus
"WATCHDOG_FINISHED=$(Get-Date -Format o)`nSTATUS=$($result.status)" | Add-Content -Encoding UTF8 "$heartbeatDir/latest.txt"
