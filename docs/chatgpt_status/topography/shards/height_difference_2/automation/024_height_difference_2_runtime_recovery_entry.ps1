[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$sourceRootText = [string]$env:AAYS_REPO_ROOT
if (-not $sourceRootText) { throw 'HEIGHT_DIFFERENCE_2_REPO_ROOT_MISSING' }
$sourceRoot = [System.IO.Path]::GetFullPath($sourceRootText)
$activeRoot = 'F:\chatgpt\chat_gpt_clone_1_main'
$watchWorktree = 'F:\chatgpt\aays1_repo_to_bridge_watch_worktree'
$bridgeRoot = 'F:\AAYS_GITHUB_BRIDGE_CLEAN2'

foreach ($path in @($sourceRoot,$activeRoot,$watchWorktree,$bridgeRoot)) {
  if (-not (Test-Path -LiteralPath $path)) { throw "HEIGHT_DIFFERENCE_2_RUNTIME_PATH_MISSING=$path" }
}

$pythonCommand = $null
$pythonPrefix = @()
foreach ($name in @('python','py','python3')) {
  $candidate = Get-Command $name -ErrorAction SilentlyContinue
  if ($candidate) {
    $pythonCommand = $candidate.Source
    if ($name -eq 'py') { $pythonPrefix = @('-3') }
    break
  }
}
if (-not $pythonCommand) { throw 'HEIGHT_DIFFERENCE_2_PYTHON_NOT_AVAILABLE' }

$taskJson = Join-Path $sourceRoot 'docs\chatgpt_status\aays1\queue\aays1_height_difference_2_canonical_export_official_sampling_20260720.task.json'
$branchRecovery = Join-Path $sourceRoot 'docs\chatgpt_status\topography\shards\height_difference_2\automation\020_prepare_branch_aware_same_task_bridge.py'
$runtimeRecovery = Join-Path $sourceRoot 'docs\chatgpt_status\topography\shards\height_difference_2\automation\022_apply_same_task_runtime_recovery.py'
$receiptVerifier = Join-Path $sourceRoot 'docs\chatgpt_status\topography\shards\height_difference_2\automation\023_verify_same_task_runtime_receipt.py'
$outputDir = Join-Path $sourceRoot 'docs\chatgpt_status\topography\shards\height_difference_2\runner_outputs'
$branchRecoveryOutput = Join-Path $outputDir '010_same_task_bridge_recovery_latest.json'
$runtimeRecoveryOutput = Join-Path $outputDir '011_same_task_runtime_recovery_latest.json'
$receiptOutput = Join-Path $outputDir '012_same_task_runtime_receipt_latest.json'
$entryOutput = Join-Path $outputDir '013_runtime_recovery_entrypoint_latest.json'

foreach ($file in @($taskJson,$branchRecovery,$runtimeRecovery,$receiptVerifier)) {
  if (-not (Test-Path -LiteralPath $file)) { throw "HEIGHT_DIFFERENCE_2_RUNTIME_FILE_MISSING=$file" }
}
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

& $pythonCommand @pythonPrefix $runtimeRecovery `
  --source-repo-root $sourceRoot `
  --active-repo-root $activeRoot `
  --watch-worktree $watchWorktree `
  --bridge-root $bridgeRoot `
  --task-json $taskJson `
  --recovery-script $branchRecovery `
  --recovery-output $branchRecoveryOutput `
  --output $runtimeRecoveryOutput `
  --apply
if ($LASTEXITCODE -ne 0) { throw "HEIGHT_DIFFERENCE_2_RUNTIME_RECOVERY_EXIT_$LASTEXITCODE" }

$runtime = Get-Content -LiteralPath $runtimeRecoveryOutput -Raw | ConvertFrom-Json
$bridgeTask = [string]$runtime.bridge_task_path
if (-not $bridgeTask -or -not (Test-Path -LiteralPath $bridgeTask)) { throw 'HEIGHT_DIFFERENCE_2_BRIDGE_TASK_RECEIPT_MISSING' }

& $pythonCommand @pythonPrefix $receiptVerifier `
  --runtime-recovery $runtimeRecoveryOutput `
  --bridge-task $bridgeTask `
  --output $receiptOutput
if ($LASTEXITCODE -ne 0) { throw "HEIGHT_DIFFERENCE_2_RUNTIME_RECEIPT_EXIT_$LASTEXITCODE" }

$receipt = Get-Content -LiteralPath $receiptOutput -Raw | ConvertFrom-Json
$payload = [ordered]@{
  schema_version = 1
  slot_id = 'height_difference_2'
  task_id = $taskId
  attempt_id = 'height-difference-2-20260721-014'
  status = 'SAME_TASK_RUNTIME_RECOVERY_ENTRYPOINT_COMPLETED'
  runtime_recovery_status = [string]$runtime.status
  runtime_receipt_status = [string]$receipt.status
  bridge_task_path = $bridgeTask
  ready_for_claim = $true
  existing_worktree_reused = $true
  existing_bridge_reused = $true
  process_started = $false
  new_worktree_created = $false
  new_runner = $false
  parallel_runner = $false
  new_task_created = $false
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $entryOutput -Encoding UTF8
Write-Output ($payload | ConvertTo-Json -Depth 8)
