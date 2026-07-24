[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Write-Json([string]$Path, [object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText(
    $Path,
    (($Value | ConvertTo-Json -Depth 80) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
}

function Update-QueueStatus([string]$QueuePath, [string]$Status, [string]$Blocker, [string]$ReportPath) {
  if (-not (Test-Path -LiteralPath $QueuePath)) { return }
  $queue = Get-Content -LiteralPath $QueuePath -Raw -Encoding UTF8 | ConvertFrom-Json
  $queue.status = $Status
  $queue | Add-Member -NotePropertyName dispatcher_updated_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
  if ($Blocker) {
    $queue | Add-Member -NotePropertyName blocker -NotePropertyValue $Blocker -Force
  } elseif ($queue.PSObject.Properties.Name -contains 'blocker') {
    $queue.blocker = $null
  }
  if ($ReportPath) {
    $queue | Add-Member -NotePropertyName dispatcher_report_path -NotePropertyValue $ReportPath -Force
  }
  $queue.final_ready = $false
  if ($queue.PSObject.Properties.Name -contains 'product_final_ready') { $queue.product_final_ready = $false }
  if ($queue.PSObject.Properties.Name -contains 'fake_data') { $queue.fake_data = $false }
  Write-Json $QueuePath $queue
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$dispatcherTaskId = [string]$env:AAYS_TASK_ID
$originalPageKey = [string]$env:AAYS_PAGE_KEY
$branch = [string]$env:AAYS_TARGET_BRANCH

if (-not $repoRoot -or -not $dispatcherTaskId -or $originalPageKey -ne '_shared') {
  throw 'GAS_EMISSIONS_DISPATCH_MUST_RUN_FROM_SHARED_CANONICAL_QUEUE'
}
if ($branch -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_DISPATCH_WRONG_BRANCH'
}

$reportRel = 'docs/chatgpt_status/_shared/reports/gas_emissions_canonical_dispatch_20260711_latest.json'
$statusRel = 'docs/chatgpt_status/_shared/status/gas_emissions_canonical_dispatch_20260711_latest.json'
$reportPath = Join-Path $repoRoot ($reportRel -replace '/', '\')
$statusPath = Join-Path $repoRoot ($statusRel -replace '/', '\')

$stages = @(
  [ordered]@{
    name = 'publish_and_browser_smoke_28'
    task_id = 'gas_emissions_28_publish_and_browser_smoke_20260711_02'
    script = 'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_28_PUBLISH_AND_BROWSER_SMOKE_20260711_V2.ps1'
    queue = 'docs/chatgpt_status/gas_emissions/queue/gas_emissions_28_publish_and_browser_smoke_20260711_02.task.json'
    expected_rows = 28
  },
  [ordered]@{
    name = 'official_csv_and_browser_smoke_37'
    task_id = 'gas_emissions_37_multi_stage_pipeline_20260711_01'
    script = 'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_37_MULTI_STAGE_PIPELINE_20260711_FIX.ps1'
    queue = 'docs/chatgpt_status/gas_emissions/queue/gas_emissions_37_multi_stage_pipeline_20260711_01.task.json'
    expected_rows = 37
  },
  [ordered]@{
    name = 'multi_batch_and_browser_smoke_66'
    task_id = 'gas_emissions_66_multi_batch_pipeline_20260711_01'
    script = 'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_66_MULTI_BATCH_PIPELINE_20260711.ps1'
    queue = 'docs/chatgpt_status/gas_emissions/queue/gas_emissions_66_multi_batch_pipeline_20260711_01.task.json'
    expected_rows = 66
  },
  [ordered]@{
    name = 'multi_batch_and_browser_smoke_100'
    task_id = 'gas_emissions_100_multi_batch_pipeline_20260711_01'
    script = 'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_100_MULTI_BATCH_PIPELINE_20260711.ps1'
    queue = 'docs/chatgpt_status/gas_emissions/queue/gas_emissions_100_multi_batch_pipeline_20260711_01.task.json'
    expected_rows = 100
  },
  [ordered]@{
    name = 'multi_batch_and_browser_smoke_151'
    task_id = 'gas_emissions_151_multi_batch_pipeline_20260711_01'
    script = 'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_151_MULTI_BATCH_PIPELINE_20260711.ps1'
    queue = 'docs/chatgpt_status/gas_emissions/queue/gas_emissions_151_multi_batch_pipeline_20260711_01.task.json'
    expected_rows = 151
  }
)

$payload = [ordered]@{
  dispatcher_task_id = $dispatcherTaskId
  page_key = '_shared'
  target_page_key = 'gas_emissions'
  target_branch = $branch
  status = 'RUNNING'
  generated_by_runner = $true
  started_at = (Get-Date).ToUniversalTime().ToString('o')
  stages_total = $stages.Count
  stages_completed = 0
  current_stage = $null
  stage_results = @()
  blocker = $null
  single_runner_only = $true
  new_runner = $false
  parallel_runner = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json $reportPath $payload
Write-Json $statusPath $payload

$originalTaskId = [string]$env:AAYS_TASK_ID
$originalTargetPage = [string]$env:AAYS_PAGE_KEY
$failed = $false

foreach ($stage in $stages) {
  $payload.current_stage = $stage.name
  $scriptPath = Join-Path $repoRoot ($stage.script -replace '/', '\')
  $queuePath = Join-Path $repoRoot ($stage.queue -replace '/', '\')
  if (-not (Test-Path -LiteralPath $scriptPath)) {
    $blocker = "MISSING_STAGE_SCRIPT: $($stage.script)"
    $payload.status = 'BLOCKED_MISSING_STAGE_SCRIPT'
    $payload.blocker = $blocker
    $payload.stage_results += [ordered]@{ name=$stage.name; status='BLOCKED'; blocker=$blocker; expected_rows=$stage.expected_rows }
    Update-QueueStatus $queuePath 'blocked' $blocker $reportRel
    $failed = $true
    break
  }

  Update-QueueStatus $queuePath 'running' $null $reportRel
  $env:AAYS_PAGE_KEY = 'gas_emissions'
  $env:AAYS_TASK_ID = [string]$stage.task_id
  $stageStarted = (Get-Date).ToUniversalTime().ToString('o')
  $stageOutput = @()
  $stageError = $null
  $passed = $false
  try {
    $stageOutput = @(& $scriptPath 2>&1 | ForEach-Object { [string]$_ })
    $passed = $true
  } catch {
    $stageError = $_.Exception.Message
    $stageOutput += [string]$_
    $passed = $false
  } finally {
    $env:AAYS_PAGE_KEY = $originalTargetPage
    $env:AAYS_TASK_ID = $originalTaskId
  }

  $tail = @($stageOutput | Select-Object -Last 30)
  if ($passed) {
    $payload.stages_completed = [int]$payload.stages_completed + 1
    $payload.stage_results += [ordered]@{
      name = $stage.name
      task_id = $stage.task_id
      status = 'PASS'
      expected_rows = $stage.expected_rows
      started_at = $stageStarted
      completed_at = (Get-Date).ToUniversalTime().ToString('o')
      output_tail = $tail
    }
    Update-QueueStatus $queuePath 'completed' $null $reportRel
  } else {
    $blocker = "STAGE_FAILED: $($stage.name): $stageError"
    $payload.status = 'BLOCKED_STAGE_FAILED'
    $payload.blocker = $blocker
    $payload.stage_results += [ordered]@{
      name = $stage.name
      task_id = $stage.task_id
      status = 'BLOCKED'
      expected_rows = $stage.expected_rows
      started_at = $stageStarted
      failed_at = (Get-Date).ToUniversalTime().ToString('o')
      blocker = $blocker
      output_tail = $tail
    }
    Update-QueueStatus $queuePath 'blocked' $blocker $reportRel
    $failed = $true
  }

  Write-Json $reportPath $payload
  Write-Json $statusPath $payload
  if ($failed) { break }
}

$env:AAYS_PAGE_KEY = $originalTargetPage
$env:AAYS_TASK_ID = $originalTaskId
$payload.current_stage = $null
$payload.completed_at = (Get-Date).ToUniversalTime().ToString('o')
if (-not $failed -and [int]$payload.stages_completed -eq $stages.Count) {
  $payload.status = 'PASS_GAS_EMISSIONS_151_CHAIN'
  $payload.blocker = $null
} elseif (-not $payload.blocker) {
  $payload.status = 'BLOCKED_INCOMPLETE_CHAIN'
  $payload.blocker = 'Dispatcher ended before every stage produced real PASS evidence.'
}
$payload.final_ready = $false
$payload.product_final_ready = $false
$payload.fake_data = $false
Write-Json $reportPath $payload
Write-Json $statusPath $payload

if ($failed) {
  throw $payload.blocker
}
Write-Output ($payload | ConvertTo-Json -Depth 80)
