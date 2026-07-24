[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}

function Write-Json([string]$Path,[object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText($Path,(($Value | ConvertTo-Json -Depth 100)+"`n"),[System.Text.UTF8Encoding]::new($false))
}

function Get-VisibleCount([string]$Path) {
  $o = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
  return @($o.rows).Count
}

function Get-BrowserProofCount([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return -1 }
  try {
    $o = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($o.browser_smoke_passed -eq $true -and $null -ne $o.browser_smoke_row_count) { return [int]$o.browser_smoke_row_count }
  } catch {}
  return -1
}

function Update-Queue([string]$Path,[string]$State,[string]$Blocker,[string]$ReportRel) {
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $q = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
  $q | Add-Member -NotePropertyName status -NotePropertyValue $State -Force
  $q | Add-Member -NotePropertyName dispatcher_v5_updated_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
  $q | Add-Member -NotePropertyName dispatcher_report_path -NotePropertyValue $ReportRel -Force
  $q | Add-Member -NotePropertyName blocker -NotePropertyValue $Blocker -Force
  foreach ($name in @('final_ready','product_final_ready','fake_data','db_write','migration','production_deploy')) {
    $q | Add-Member -NotePropertyName $name -NotePropertyValue $false -Force
  }
  Write-Json $Path $q
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$dispatcherTaskId = [string]$env:AAYS_TASK_ID
$originalPageKey = [string]$env:AAYS_PAGE_KEY
$branch = [string]$env:AAYS_TARGET_BRANCH
if (-not $repoRoot -or -not $dispatcherTaskId -or $originalPageKey -ne '_shared') { throw 'GAS_EMISSIONS_DISPATCH_V5_WRONG_CONTEXT' }
if ($branch -ne 'codex/aays-single-runner-v5-20260706') { throw 'GAS_EMISSIONS_DISPATCH_V5_WRONG_BRANCH' }
if (-not [string]$env:AAYS_CONTROLLER_REPO_ROOT) { throw 'AAYS_CONTROLLER_REPO_ROOT_MISSING' }

$rowsRel = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
$statusRel = 'england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
$pipelineRel = 'england_map_web/data/program_layer_matrix/gas_emissions_pipeline_latest.json'
$rowsPath = Join-Path $repoRoot ($rowsRel -replace '/','\')
$statusPath = Join-Path $repoRoot ($statusRel -replace '/','\')
$pipelinePath = Join-Path $repoRoot ($pipelineRel -replace '/','\')
if (-not (Test-Path -LiteralPath $rowsPath)) { throw 'GAS_EMISSIONS_ROWS_NOT_FOUND' }
if ((Get-VisibleCount $rowsPath) -lt 37) { throw 'GAS_EMISSIONS_V5_REQUIRES_37_PROVEN_ROWS' }

$genericProofRel = 'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_PUBLISH_CURRENT_AND_BROWSER_PROOF_20260713.ps1'
$genericProofPath = Join-Path $repoRoot ($genericProofRel -replace '/','\')
if (-not (Test-Path -LiteralPath $genericProofPath)) { throw 'GENERIC_PUBLISH_PROOF_SCRIPT_NOT_FOUND' }

$stages = @(
  [ordered]@{ name='multi_batch_66'; task_id='gas_emissions_66_multi_batch_pipeline_20260711_01'; prerequisite=37; target=66; expected_new=29; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_66_MULTI_BATCH_PIPELINE_20260713_TYPE_FIX.ps1'; queue='docs/chatgpt_status/gas_emissions/queue/gas_emissions_66_multi_batch_pipeline_20260711_01.task.json' },
  [ordered]@{ name='multi_batch_100'; task_id='gas_emissions_100_multi_batch_pipeline_20260711_01'; prerequisite=66; target=100; expected_new=34; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_100_MULTI_BATCH_PIPELINE_20260713_TYPE_CONTROLLER_FIX.ps1'; queue='docs/chatgpt_status/gas_emissions/queue/gas_emissions_100_multi_batch_pipeline_20260711_01.task.json' },
  [ordered]@{ name='multi_batch_151'; task_id='gas_emissions_151_multi_batch_pipeline_20260711_01'; prerequisite=100; target=151; expected_new=51; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_151_MULTI_BATCH_PIPELINE_20260713_CONTROLLER_FIX.ps1'; queue='docs/chatgpt_status/gas_emissions/queue/gas_emissions_151_multi_batch_pipeline_20260711_01.task.json' },
  [ordered]@{ name='year_2007_233'; task_id='gas_emissions_233_year2007_pipeline_20260711_01'; prerequisite=151; target=233; expected_new=82; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_YEAR_SELECTOR_EXPANSION_20260713_TYPE_CONTROLLER_FIX.ps1'; queue='docs/chatgpt_status/gas_emissions/queue/gas_emissions_233_year2007_pipeline_20260711_01.task.json' },
  [ordered]@{ name='year_2008_316'; task_id='gas_emissions_316_year2008_pipeline_20260711_01'; prerequisite=233; target=316; expected_new=83; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_YEAR_SELECTOR_EXPANSION_20260713_TYPE_CONTROLLER_FIX.ps1'; queue='docs/chatgpt_status/gas_emissions/queue/gas_emissions_316_year2008_pipeline_20260711_01.task.json' }
)

$reportRel = 'docs/chatgpt_status/_shared/reports/gas_emissions_canonical_dispatch_v5_20260713_latest.json'
$resultStatusRel = 'docs/chatgpt_status/_shared/status/gas_emissions_canonical_dispatch_v5_20260713_latest.json'
$reportPath = Join-Path $repoRoot ($reportRel -replace '/','\')
$resultStatusPath = Join-Path $repoRoot ($resultStatusRel -replace '/','\')

$payload = [ordered]@{
  dispatcher_task_id=$dispatcherTaskId
  dispatcher_version='v5_20260713'
  page_key='_shared'
  target_page_key='gas_emissions'
  target_branch=$branch
  status='RUNNING'
  started_at=(Get-Date).ToUniversalTime().ToString('o')
  initial_visible_rows=(Get-VisibleCount $rowsPath)
  target_visible_rows=316
  stages_total=7
  previously_completed_stages=2
  stages_completed_this_run=0
  stages_skipped_proven=0
  current_stage=$null
  stage_results=@()
  blocker=$null
  single_runner_only=$true
  new_runner=$false
  parallel_runner=$false
  parcel_binding_gate_passed=$false
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
    dispatcher_task_id=$dispatcherTaskId
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
    source='GOV.UK DESNZ 2005 to 2023 local authority greenhouse gas emissions dataset'
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

$originalTaskId = [string]$env:AAYS_TASK_ID
$failed = $false
foreach ($stage in $stages) {
  $current = Get-VisibleCount $rowsPath
  $proof = Get-BrowserProofCount $statusPath
  $payload.current_stage = $stage.name
  $queuePath = Join-Path $repoRoot ($stage.queue -replace '/','\')
  $scriptPath = Join-Path $repoRoot ($stage.script -replace '/','\')

  if ($current -gt [int]$stage.target -or ($current -eq [int]$stage.target -and $proof -ge [int]$stage.target)) {
    $payload.stages_skipped_proven = [int]$payload.stages_skipped_proven + 1
    $payload.stage_results += [ordered]@{ name=$stage.name; task_id=$stage.task_id; status='SKIPPED_ALREADY_PROVEN'; observed_rows=$current; browser_proof_rows=$proof; target_rows=[int]$stage.target; checked_at=(Get-Date).ToUniversalTime().ToString('o') }
    Update-Queue $queuePath 'completed' $null $reportRel
    Write-State
    continue
  }

  if ($current -lt [int]$stage.prerequisite) {
    $payload.status='BLOCKED_PREREQUISITE'
    $payload.blocker="PREREQUISITE_VISIBLE_ROWS_NOT_MET: stage=$($stage.name) current=$current required=$($stage.prerequisite)"
    $payload.stage_results += [ordered]@{ name=$stage.name; task_id=$stage.task_id; status='BLOCKED'; blocker=$payload.blocker }
    Update-Queue $queuePath 'blocked' $payload.blocker $reportRel
    $failed=$true
    Write-State
    break
  }

  $stageStarted=(Get-Date).ToUniversalTime().ToString('o')
  $stageOutput=@()
  $stageError=$null
  Update-Queue $queuePath 'running' $null $reportRel
  Write-State

  if ($current -eq [int]$stage.prerequisite) {
    if (-not (Test-Path -LiteralPath $scriptPath)) {
      $stageError="MISSING_STAGE_SCRIPT: $($stage.script)"
    } else {
      $env:AAYS_PAGE_KEY='gas_emissions'
      $env:AAYS_TASK_ID=[string]$stage.task_id
      try {
        $stageOutput=@(& $scriptPath 2>&1 | ForEach-Object { [string]$_ })
      } catch {
        $stageError=$_.Exception.Message
        $stageOutput += [string]$_
      } finally {
        $env:AAYS_PAGE_KEY=$originalPageKey
        $env:AAYS_TASK_ID=$originalTaskId
      }
    }
  }

  $afterStage = Get-VisibleCount $rowsPath
  if ($afterStage -eq [int]$stage.target) {
    $env:AAYS_PAGE_KEY='gas_emissions'
    $env:AAYS_TASK_ID=([string]$stage.task_id + '_live_publish_proof')
    try {
      $proofOutput=@(& $genericProofPath -ExpectedRows ([int]$stage.target) 2>&1 | ForEach-Object { [string]$_ })
      $stageOutput += $proofOutput
    } catch {
      if (-not $stageError) { $stageError=$_.Exception.Message }
      $stageOutput += [string]$_
    } finally {
      $env:AAYS_PAGE_KEY=$originalPageKey
      $env:AAYS_TASK_ID=$originalTaskId
    }
  }

  $afterCount=Get-VisibleCount $rowsPath
  $afterProof=Get-BrowserProofCount $statusPath
  $tail=@($stageOutput | Select-Object -Last 50)
  if ($afterCount -eq [int]$stage.target -and $afterProof -ge [int]$stage.target) {
    $payload.stages_completed_this_run=[int]$payload.stages_completed_this_run + 1
    $payload.stage_results += [ordered]@{
      name=$stage.name; task_id=$stage.task_id; status='PASS'; expected_new_rows=[int]$stage.expected_new;
      visible_rows_before=$current; visible_rows_after=$afterCount; browser_proof_rows=$afterProof; target_rows=[int]$stage.target;
      started_at=$stageStarted; completed_at=(Get-Date).ToUniversalTime().ToString('o'); recovered_stage_error=$stageError; output_tail=$tail
    }
    Update-Queue $queuePath 'completed' $null $reportRel
    $payload.status='RUNNING'
    $payload.blocker=$null
  } else {
    if (-not $stageError) { $stageError="TARGET_OR_BROWSER_PROOF_NOT_REACHED: rows=$afterCount proof=$afterProof target=$($stage.target)" }
    $payload.status='BLOCKED_STAGE_FAILED'
    $payload.blocker="STAGE_FAILED: $($stage.name): $stageError"
    $payload.stage_results += [ordered]@{
      name=$stage.name; task_id=$stage.task_id; status='BLOCKED'; visible_rows_before=$current; visible_rows_after=$afterCount;
      browser_proof_rows=$afterProof; target_rows=[int]$stage.target; started_at=$stageStarted;
      failed_at=(Get-Date).ToUniversalTime().ToString('o'); blocker=$payload.blocker; output_tail=$tail
    }
    Update-Queue $queuePath 'blocked' $payload.blocker $reportRel
    $failed=$true
  }
  Write-State
  if ($failed) { break }
}

$env:AAYS_PAGE_KEY=$originalPageKey
$env:AAYS_TASK_ID=$originalTaskId
$payload.current_stage=$null
$payload.completed_at=(Get-Date).ToUniversalTime().ToString('o')
$payload.final_visible_rows=Get-VisibleCount $rowsPath
$payload.final_browser_proof_rows=Get-BrowserProofCount $statusPath
if (-not $failed -and [int]$payload.final_visible_rows -eq 316 -and [int]$payload.final_browser_proof_rows -ge 316) {
  $payload.status='PASS_GAS_EMISSIONS_316_SOURCE_ROW_CHAIN'
  $payload.blocker='PARCEL_BINDING_EVIDENCE_STILL_REQUIRED'
} elseif (-not $payload.blocker) {
  $payload.status='BLOCKED_INCOMPLETE_CHAIN'
  $payload.blocker="Dispatcher ended before 316 browser-proven source rows; rows=$($payload.final_visible_rows) proof=$($payload.final_browser_proof_rows)."
}
$payload.final_ready=$false
$payload.product_final_ready=$false
$payload.fake_data=$false
Write-State
if ($failed) { throw $payload.blocker }
Write-Output ($payload | ConvertTo-Json -Depth 100)
