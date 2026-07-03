param(
  [string]$RepoRoot = $(if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { 'F:\chatgpt\chat_gpt_clone_1_main' }),
  [string]$TaskId = 'security_public_safety_batch_TEMPLATE'
)

$ErrorActionPreference = 'Stop'
$PageKey = 'security_public_safety'
$ReportDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\reports"
$StatusDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
$WebUpdateDir = Join-Path $RepoRoot 'outputs\england_program_parcel_matrix_20260629\security_public_safety_updates'
New-Item -ItemType Directory -Force -Path $ReportDir, $StatusDir, $WebUpdateDir | Out-Null

$ReportPath = Join-Path $ReportDir "$TaskId.md"
$StatusPath = Join-Path $StatusDir "$TaskId.status.json"
$LatestChangesPath = Join-Path $WebUpdateDir 'latest_changes.json'

@"
page_key=$PageKey
task_id=$TaskId
status=TEMPLATE_ONLY_NOT_EXECUTED_AS_FINAL
final_ready=false
fake_data=false
db_write=false
ddl=false
migration_apply=false
prod_deploy=false
next_single_action=Replace this template with a real read-only batch processor that writes verified aggregate public-safety evidence.
"@ | Set-Content -LiteralPath $ReportPath -Encoding UTF8

@{
  page_key = $PageKey
  task_id = $TaskId
  status = 'template_only'
  final_ready = $false
  fake_data = $false
  generated_at = (Get-Date).ToString('o')
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $StatusPath -Encoding UTF8

if (-not (Test-Path -LiteralPath $LatestChangesPath)) {
  @{
    layer = 'Safety / Security'
    program_output = 'Security Level percent'
    status = 'TEMPLATE_READY_WAITING_FOR_CHATGPT_RUNNER_OUTPUT'
    fake_data = $false
    summary = @{
      changed_count = 0
      verified_count = 0
      manual_review_count = 0
      accuracy_ge_3_count = 0
      final_ready = $false
    }
    changes = @()
  } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $LatestChangesPath -Encoding UTF8
}

Write-Output "REPORT=$ReportPath"
Write-Output "STATUS=$StatusPath"
Write-Output "SITE_UPDATES=$LatestChangesPath"
