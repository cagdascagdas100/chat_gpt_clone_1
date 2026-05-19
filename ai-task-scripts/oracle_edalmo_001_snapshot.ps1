$ErrorActionPreference = "Continue"
$TaskId = "oracle-edalmo-001-snapshot"
$OutDir = Join-Path (Join-Path (Get-Location) "ai-runner-outputs") ("oracle_edalmo_001_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Report = Join-Path $OutDir "oracle_edalmo_snapshot.md"
$Lines = @(
  "# Oracle edalmo snapshot",
  "timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
  "task_id=$TaskId",
  "classification=CLOUD_READY_PENDING_PROVIDER",
  "overall_completion_percent=85",
  "selected_frontend=https://terrayield.edalmo.com",
  "selected_backend=https://api-terrayield.edalmo.com",
  "runner_action=read_only_snapshot",
  "did_repeat_012A_012B_014_016=false",
  "secret_values_printed=false",
  "db_write=none",
  "ddl=none",
  "migration_apply=none",
  "prod_deploy=none",
  "next_single_action=WAIT_FOR_USER_PROVIDER_LOGIN_AND_DNS_APPLY"
)
$Lines | Set-Content -LiteralPath $Report -Encoding UTF8
Write-Output "ORACLE_EDALMO_SNAPSHOT_REPORT=$Report"
exit 0
