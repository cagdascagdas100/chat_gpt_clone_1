$ErrorActionPreference = "Continue"
$Bridge = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$PageKey = "security_public_safety_low_credit_20260612"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Base = Join-Path $Bridge "docs\chatgpt_status\$PageKey"
New-Item -ItemType Directory -Force "$Bridge\ai-results", "$Base\status", "$Base\reports", "$Base\heartbeat", "$Base\runner_output" | Out-Null
$Result = [ordered]@{
  page_key = $PageKey
  decision = "SECURITY_SHARED_RUNNER_TASK_RECEIVED"
  final_ready = $false
  complete = $false
  next = "browser_acceptance_runner_step"
  db_write = $false
  ddl = $false
  migration = $false
  production_deploy = $false
  fake_data = $false
  timestamp = $Stamp
} | ConvertTo-Json -Depth 10
$Result | Set-Content "$Bridge\ai-results\security_public_safety_browser_acceptance_latest.json" -Encoding UTF8
$Result | Set-Content "$Base\status\security_browser_acceptance_latest.md" -Encoding UTF8
$Result | Set-Content "$Base\reports\security_browser_acceptance_$Stamp.md" -Encoding UTF8
"heartbeat $Stamp" | Set-Content "$Base\heartbeat\browser_acceptance_latest.md" -Encoding UTF8
$Result | Set-Content "$Base\runner_output\security_shared_runner_task_$Stamp.txt" -Encoding UTF8
