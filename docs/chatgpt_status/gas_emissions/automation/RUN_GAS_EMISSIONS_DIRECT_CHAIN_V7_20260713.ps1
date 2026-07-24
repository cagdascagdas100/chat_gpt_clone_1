[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Write-Json([string]$Path,[object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText(
    $Path,
    (($Value | ConvertTo-Json -Depth 100) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
}

function Get-VisibleCount([string]$Path) {
  $obj = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
  return @($obj.rows).Count
}

function Get-BrowserProofCount([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return -1 }
  try {
    $obj = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($obj.browser_smoke_passed -eq $true -and $null -ne $obj.browser_smoke_row_count) {
      return [int]$obj.browser_smoke_row_count
    }
  } catch {}
  return -1
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$rootTaskId = [string]$env:AAYS_TASK_ID
$pageKey = [string]$env:AAYS_PAGE_KEY
$branch = [string]$env:AAYS_TARGET_BRANCH

if (-not $repoRoot -or -not $rootTaskId -or $pageKey -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V7_WRONG_CONTEXT'
}
if ($branch -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V7_WRONG_BRANCH'
}

$rowsRel = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
$statusRel = 'england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
$pipelineRel = 'england_map_web/data/program_layer_matrix/gas_emissions_pipeline_latest.json'
$rowsPath = Join-Path $repoRoot ($rowsRel -replace '/','\')
$statusPath = Join-Path $repoRoot ($statusRel -replace '/','\')
$pipelinePath = Join-Path $repoRoot ($pipelineRel -replace '/','\')

if (-not (Test-Path -LiteralPath $rowsPath)) { throw 'GAS_EMISSIONS_ROWS_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $statusPath)) { throw 'GAS_EMISSIONS_STATUS_NOT_FOUND' }

$proofRel = 'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_PUBLISH_CURRENT_AND_BROWSER_PROOF_20260713_DOM_READY_FIX.ps1'
$proofPath = Join-Path $repoRoot ($proofRel -replace '/','\')
if (-not (Test-Path -LiteralPath $proofPath)) { throw 'GAS_EMISSIONS_DOM_READY_PROOF_NOT_FOUND' }

$stages = @(
  [ordered]@{ name='browser_proof_66'; prerequisite=37; target=66; expected_new=29; script=$null; task_id='gas_emissions_66_multi_batch_pipeline_20260711_01' },
  [ordered]@{ name='multi_batch_100'; prerequisite=66; target=100; expected_new=34; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_100_MULTI_BATCH_PIPELINE_20260713_TYPE_CONTROLLER_FIX.ps1'; task_id='gas_emissions_100_multi_batch_pipeline_20260711_01' },
  [ordered]@{ name='multi_batch_151'; prerequisite=100; target=151; expected_new=51; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_151_MULTI_BATCH_PIPELINE_20260713_CONTROLLER_FIX.ps1'; task_id='gas_emissions_151_multi_batch_pipeline_20260711_01' },
  [ordered]@{ name='year_2007_233'; prerequisite=151; target=233; expected_new=82; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_YEAR_SELECTOR_EXPANSION_20260713_TYPE_CONTROLLER_FIX.ps1'; task_id='gas_emissions_233_year2007_pipeline_20260711_01' },
  [ordered]@{ name='year_2008_316'; prerequisite=233; target=316; expected_new=83; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_YEAR_SELECTOR_EXPANSION_20260713_TYPE_CONTROLLER_FIX.ps1'; task_id='gas_emissions_316_year2008_pipeline_20260711_01' }
)

$reportRel = 'docs/chatgpt_status/gas_emissions/reports/178_gas_emissions_direct_chain_v7_20260713_latest.json'
$resultStatusRel = 'docs/chatgpt_status/gas_emissions/status/178_gas_emissions_direct_chain_v7_20260713_latest.json'
$reportPath = Join-Path $repoRoot ($reportRel -replace '/','\')
$resultStatusPath = Join-Path $repoRoot ($resultStatusRel -replace '/','\')

$payload = [ordered]@{
  task_id=$rootTaskId
  page_key='gas_emissions'
  chain_version='v7_20260713'
  target_branch=$branch
  status='RUNNING'
  started_at=(Get-Date).ToUniversalTime().ToString('o')
  initial_visible_rows=(Get-VisibleCount $rowsPath)
  initial_browser_proof_rows=(Get-BrowserProofCount $statusPath)
  target_visible_rows=316
  stages_total=7
  previously_completed_stages=2
  stages_completed_this_run=0
  stages_skipped_proven=0
  current_stage=$null
  stage_results=@()
  blocker=$null
  source='GOV.UK DESNZ 2005 to 2023 local authority greenhouse gas emissions dataset'
  source_accuracy_score_4='3.4/4'
  target_confidence_percent=94
  parcel_binding_gate_passed=$false
  single_runner_only=$true
  new_runner=$false
  parallel_runner=$false
  final_ready=$false
  product_final_ready=$false
  fake_data=$false
  db_write=$false
  migration=$false
  production_deploy=$false
}

function Write-State {
  $pipeline = [ordered]@{
    layer='Gas Emissions'
    task_id=$rootTaskId
    chain_version='v7_20260713'
    status=$payload.status
    current_verified_rows=(Get-VisibleCount $rowsPath)
    browser_proof_rows=(Get-BrowserProofCount $statusPath)
    target_verified_rows=316
    stages_total=7
    previously_completed_stages=2
    stages_completed_this_run=$payload.stages_completed_this_run
    stages_skipped_proven=$payload.stages_skipped_proven
    current_stage=$payload.current_stage
    stage_results=$payload.stage_results
    blocker=$payload.blocker
    source=$payload.source
    source_accuracy_score_4='3.4/4'
    target_confidence_percent=94
    parcel_binding_gate_passed=$false
    final_ready=$false
    product_final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
    updated_at=(Get-Date).ToUniversalTime().ToString('o')
  }
  Write-Json $reportPath $payload
  Write-Json $resultStatusPath $payload
  Write-Json $pipelinePath $pipeline
}

Write-State
$failed = $false
$originalTaskId = $rootTaskId

foreach ($stage in $stages) {
  $current = Get-VisibleCount $rowsPath
  $proof = Get-BrowserProofCount $statusPath
  $payload.current_stage = [string]$stage.name
  Write-State

  if ($current -gt [int]$stage.target -or ($current -eq [int]$stage.target -and $proof -ge [int]$stage.target)) {
    $payload.stages_skipped_proven = [int]$payload.stages_skipped_proven + 1
    $payload.stage_results += [ordered]@{
      name=$stage.name; task_id=$stage.task_id; status='SKIPPED_ALREADY_PROVEN';
      observed_rows=$current; browser_proof_rows=$proof; target_rows=[int]$stage.target;
      checked_at=(Get-Date).ToUniversalTime().ToString('o')
    }
    Write-State
    continue
  }

  if ($current -lt [int]$stage.prerequisite) {
    $payload.status='BLOCKED_PREREQUISITE'
    $payload.blocker="PREREQUISITE_VISIBLE_ROWS_NOT_MET: stage=$($stage.name) current=$current required=$($stage.prerequisite)"
    $payload.stage_results += [ordered]@{ name=$stage.name; task_id=$stage.task_id; status='BLOCKED'; blocker=$payload.blocker }
    $failed=$true
    Write-State
    break
  }

  $stageStarted=(Get-Date).ToUniversalTime().ToString('o')
  $stageOutput=@()
  $stageError=$null

  if ($current -eq [int]$stage.prerequisite -and $null -ne $stage.script) {
    $scriptPath = Join-Path $repoRoot ([string]$stage.script -replace '/','\')
    if (-not (Test-Path -LiteralPath $scriptPath)) {
      $stageError="MISSING_STAGE_SCRIPT: $($stage.script)"
    } else {
      $env:AAYS_TASK_ID=[string]$stage.task_id
      try {
        $stageOutput += @(& $scriptPath 2>&1 | ForEach-Object { [string]$_ })
      } catch {
        $stageError=$_.Exception.Message
        $stageOutput += [string]$_
      } finally {
        $env:AAYS_TASK_ID=$originalTaskId
      }
    }
  }

  $afterStage = Get-VisibleCount $rowsPath
  if ($afterStage -eq [int]$stage.target) {
    $env:AAYS_TASK_ID=($originalTaskId + '_' + [string]$stage.target + '_dom_ready_proof')
    try {
      $stageOutput += @(& $proofPath -ExpectedRows ([int]$stage.target) 2>&1 | ForEach-Object { [string]$_ })
    } catch {
      if (-not $stageError) { $stageError=$_.Exception.Message }
      $stageOutput += [string]$_
    } finally {
      $env:AAYS_TASK_ID=$originalTaskId
    }
  }

  $afterCount = Get-VisibleCount $rowsPath
  $afterProof = Get-BrowserProofCount $statusPath
  $tail = @($stageOutput | Select-Object -Last 60)

  if ($afterCount -eq [int]$stage.target -and $afterProof -ge [int]$stage.target) {
    $payload.stages_completed_this_run = [int]$payload.stages_completed_this_run + 1
    $payload.stage_results += [ordered]@{
      name=$stage.name; task_id=$stage.task_id; status='PASS'; expected_new_rows=[int]$stage.expected_new;
      visible_rows_before=$current; visible_rows_after=$afterCount; browser_proof_rows=$afterProof;
      target_rows=[int]$stage.target; started_at=$stageStarted;
      completed_at=(Get-Date).ToUniversalTime().ToString('o'); recovered_stage_error=$stageError;
      output_tail=$tail
    }
    $payload.status='RUNNING'
    $payload.blocker=$null
  } else {
    if (-not $stageError) {
      $stageError="TARGET_OR_BROWSER_PROOF_NOT_REACHED: rows=$afterCount proof=$afterProof target=$($stage.target)"
    }
    $payload.status='BLOCKED_STAGE_FAILED'
    $payload.blocker="STAGE_FAILED: $($stage.name): $stageError"
    $payload.stage_results += [ordered]@{
      name=$stage.name; task_id=$stage.task_id; status='BLOCKED';
      visible_rows_before=$current; visible_rows_after=$afterCount; browser_proof_rows=$afterProof;
      target_rows=[int]$stage.target; started_at=$stageStarted;
      failed_at=(Get-Date).ToUniversalTime().ToString('o'); blocker=$payload.blocker;
      output_tail=$tail
    }
    $failed=$true
  }
  Write-State
  if ($failed) { break }
}

$env:AAYS_TASK_ID=$originalTaskId
$payload.current_stage=$null
$payload.completed_at=(Get-Date).ToUniversalTime().ToString('o')
$payload.final_visible_rows=Get-VisibleCount $rowsPath
$payload.final_browser_proof_rows=Get-BrowserProofCount $statusPath
if (-not $failed -and [int]$payload.final_visible_rows -eq 316 -and [int]$payload.final_browser_proof_rows -ge 316) {
  $payload.status='PASS_GAS_EMISSIONS_316_CHAIN'
  $payload.blocker='PARCEL_BINDING_EVIDENCE_STILL_REQUIRED'
} elseif (-not $payload.blocker) {
  $payload.status='BLOCKED_INCOMPLETE_CHAIN'
  $payload.blocker="Direct chain ended before 316 browser-proven rows; rows=$($payload.final_visible_rows) proof=$($payload.final_browser_proof_rows)."
}
$payload.final_ready=$false
$payload.product_final_ready=$false
$payload.fake_data=$false
$payload.db_write=$false
$payload.migration=$false
$payload.production_deploy=$false
Write-State

if ($failed) { throw $payload.blocker }
Write-Output ($payload | ConvertTo-Json -Depth 100)
