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

function Get-BrowserProofCount([string]$StatusPath) {
  if (-not (Test-Path -LiteralPath $StatusPath)) { return -1 }
  try {
    $status = Get-Content -LiteralPath $StatusPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($status.browser_smoke_passed -eq $true -and $null -ne $status.browser_smoke_row_count) {
      return [int]$status.browser_smoke_row_count
    }
  } catch {}
  return -1
}

function Update-Queue([string]$Path,[string]$State,[string]$Blocker,[string]$ReportRel) {
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $q = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
  $q | Add-Member -NotePropertyName status -NotePropertyValue $State -Force
  $q | Add-Member -NotePropertyName dispatcher_v3_updated_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
  $q | Add-Member -NotePropertyName dispatcher_report_path -NotePropertyValue $ReportRel -Force
  $q | Add-Member -NotePropertyName blocker -NotePropertyValue $Blocker -Force
  $q | Add-Member -NotePropertyName final_ready -NotePropertyValue $false -Force
  $q | Add-Member -NotePropertyName product_final_ready -NotePropertyValue $false -Force
  $q | Add-Member -NotePropertyName fake_data -NotePropertyValue $false -Force
  $q | Add-Member -NotePropertyName db_write -NotePropertyValue $false -Force
  $q | Add-Member -NotePropertyName migration -NotePropertyValue $false -Force
  $q | Add-Member -NotePropertyName production_deploy -NotePropertyValue $false -Force
  Write-Json $Path $q
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$dispatcherTaskId = [string]$env:AAYS_TASK_ID
$originalPageKey = [string]$env:AAYS_PAGE_KEY
$branch = [string]$env:AAYS_TARGET_BRANCH

if (-not $repoRoot -or -not $dispatcherTaskId -or $originalPageKey -ne '_shared') {
  throw 'GAS_EMISSIONS_DISPATCH_V3_MUST_RUN_FROM_SHARED_CANONICAL_QUEUE'
}
if ($branch -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_DISPATCH_V3_WRONG_BRANCH'
}

$rowsRel = 'england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
$statusRel = 'england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
$rowsPath = Join-Path $repoRoot ($rowsRel -replace '/','\')
$statusPath = Join-Path $repoRoot ($statusRel -replace '/','\')
if (-not (Test-Path -LiteralPath $rowsPath)) { throw 'GAS_EMISSIONS_CANONICAL_ROWS_NOT_FOUND' }

$initialCount = Get-VisibleCount $rowsPath
if ($initialCount -lt 37) { throw "GAS_EMISSIONS_V3_REQUIRES_PROVEN_37_ROWS: $initialCount" }

$reportRel = 'docs/chatgpt_status/_shared/reports/gas_emissions_canonical_dispatch_v3_20260713_latest.json'
$resultStatusRel = 'docs/chatgpt_status/_shared/status/gas_emissions_canonical_dispatch_v3_20260713_latest.json'
$reportPath = Join-Path $repoRoot ($reportRel -replace '/','\')
$resultStatusPath = Join-Path $repoRoot ($resultStatusRel -replace '/','\')

$stages = @(
  [ordered]@{ name='proof_37'; task_id='gas_emissions_37_browser_proof_only_codex_retry_20260713_07'; prerequisite=37; target=37; script=$null; queue='docs/chatgpt_status/gas_emissions/queue/gas_emissions_37_multi_stage_pipeline_20260711_01.task.json' },
  [ordered]@{ name='multi_batch_66'; task_id='gas_emissions_66_multi_batch_pipeline_20260711_01'; prerequisite=37; target=66; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_66_MULTI_BATCH_PIPELINE_20260711.ps1'; queue='docs/chatgpt_status/gas_emissions/queue/gas_emissions_66_multi_batch_pipeline_20260711_01.task.json' },
  [ordered]@{ name='multi_batch_100'; task_id='gas_emissions_100_multi_batch_pipeline_20260711_01'; prerequisite=66; target=100; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_100_MULTI_BATCH_PIPELINE_20260711.ps1'; queue='docs/chatgpt_status/gas_emissions/queue/gas_emissions_100_multi_batch_pipeline_20260711_01.task.json' },
  [ordered]@{ name='multi_batch_151'; task_id='gas_emissions_151_multi_batch_pipeline_20260711_01'; prerequisite=100; target=151; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_151_MULTI_BATCH_PIPELINE_20260711.ps1'; queue='docs/chatgpt_status/gas_emissions/queue/gas_emissions_151_multi_batch_pipeline_20260711_01.task.json' },
  [ordered]@{ name='year_2007_233'; task_id='gas_emissions_233_year2007_pipeline_20260711_01'; prerequisite=151; target=233; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_YEAR_SELECTOR_EXPANSION_20260711.ps1'; queue='docs/chatgpt_status/gas_emissions/queue/gas_emissions_233_year2007_pipeline_20260711_01.task.json' },
  [ordered]@{ name='year_2008_316'; task_id='gas_emissions_316_year2008_pipeline_20260711_01'; prerequisite=233; target=316; script='docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_YEAR_SELECTOR_EXPANSION_20260711.ps1'; queue='docs/chatgpt_status/gas_emissions/queue/gas_emissions_316_year2008_pipeline_20260711_01.task.json' }
)

$payload = [ordered]@{
  dispatcher_task_id=$dispatcherTaskId
  dispatcher_version='v3_20260713'
  page_key='_shared'
  target_page_key='gas_emissions'
  target_branch=$branch
  status='RUNNING'
  started_at=(Get-Date).ToUniversalTime().ToString('o')
  initial_visible_rows=$initialCount
  target_visible_rows=316
  stages_total=$stages.Count
  stages_completed=0
  stages_skipped_proven=0
  current_stage=$null
  stage_results=@()
  blocker=$null
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
Write-Json $reportPath $payload
Write-Json $resultStatusPath $payload

$originalTaskId = [string]$env:AAYS_TASK_ID
$failed = $false

foreach ($stage in $stages) {
  $currentCount = Get-VisibleCount $rowsPath
  $proofCount = Get-BrowserProofCount $statusPath
  $payload.current_stage = $stage.name
  $queuePath = Join-Path $repoRoot ($stage.queue -replace '/','\')

  if ($currentCount -gt [int]$stage.target -or ($currentCount -eq [int]$stage.target -and $proofCount -ge [int]$stage.target)) {
    $payload.stages_skipped_proven = [int]$payload.stages_skipped_proven + 1
    $payload.stage_results += [ordered]@{
      name=$stage.name; task_id=$stage.task_id; status='SKIPPED_ALREADY_PROVEN'; observed_rows=$currentCount;
      browser_proof_rows=$proofCount; target_rows=[int]$stage.target; checked_at=(Get-Date).ToUniversalTime().ToString('o')
    }
    Update-Queue $queuePath 'completed' $null $reportRel
    Write-Json $reportPath $payload
    Write-Json $resultStatusPath $payload
    continue
  }

  if ($currentCount -lt [int]$stage.prerequisite) {
    $blocker = "PREREQUISITE_VISIBLE_ROWS_NOT_MET: stage=$($stage.name) current=$currentCount required=$($stage.prerequisite)"
    $payload.status='BLOCKED_PREREQUISITE'
    $payload.blocker=$blocker
    $payload.stage_results += [ordered]@{ name=$stage.name; task_id=$stage.task_id; status='BLOCKED'; blocker=$blocker }
    Update-Queue $queuePath 'blocked' $blocker $reportRel
    $failed=$true
    break
  }

  if (-not $stage.script) {
    $blocker = "PROOF_NOT_AVAILABLE_FOR_ALREADY_REACHED_STAGE: stage=$($stage.name) rows=$currentCount proof=$proofCount"
    $payload.status='BLOCKED_MISSING_PROOF'
    $payload.blocker=$blocker
    $payload.stage_results += [ordered]@{ name=$stage.name; task_id=$stage.task_id; status='BLOCKED'; blocker=$blocker }
    Update-Queue $queuePath 'blocked' $blocker $reportRel
    $failed=$true
    break
  }

  $scriptPath = Join-Path $repoRoot ($stage.script -replace '/','\')
  if (-not (Test-Path -LiteralPath $scriptPath)) {
    $blocker = "MISSING_STAGE_SCRIPT: $($stage.script)"
    $payload.status='BLOCKED_MISSING_STAGE_SCRIPT'
    $payload.blocker=$blocker
    $payload.stage_results += [ordered]@{ name=$stage.name; task_id=$stage.task_id; status='BLOCKED'; blocker=$blocker }
    Update-Queue $queuePath 'blocked' $blocker $reportRel
    $failed=$true
    break
  }

  Update-Queue $queuePath 'running' $null $reportRel
  $env:AAYS_PAGE_KEY='gas_emissions'
  $env:AAYS_TASK_ID=[string]$stage.task_id
  $started=(Get-Date).ToUniversalTime().ToString('o')
  $output=@()
  $errorText=$null
  $passed=$false
  try {
    $output=@(& $scriptPath 2>&1 | ForEach-Object { [string]$_ })
    $passed=$true
  } catch {
    $errorText=$_.Exception.Message
    $output += [string]$_
  } finally {
    $env:AAYS_PAGE_KEY=$originalPageKey
    $env:AAYS_TASK_ID=$originalTaskId
  }

  $afterCount=Get-VisibleCount $rowsPath
  $afterProof=Get-BrowserProofCount $statusPath
  $tail=@($output | Select-Object -Last 40)
  if ($passed -and $afterCount -eq [int]$stage.target -and $afterProof -ge [int]$stage.target) {
    $payload.stages_completed=[int]$payload.stages_completed + 1
    $payload.stage_results += [ordered]@{
      name=$stage.name; task_id=$stage.task_id; status='PASS'; visible_rows_before=$currentCount;
      visible_rows_after=$afterCount; browser_proof_rows=$afterProof; target_rows=[int]$stage.target;
      started_at=$started; completed_at=(Get-Date).ToUniversalTime().ToString('o'); output_tail=$tail
    }
    Update-Queue $queuePath 'completed' $null $reportRel
  } else {
    if (-not $errorText) { $errorText="TARGET_OR_BROWSER_PROOF_NOT_REACHED: rows=$afterCount proof=$afterProof target=$($stage.target)" }
    $blocker="STAGE_FAILED: $($stage.name): $errorText"
    $payload.status='BLOCKED_STAGE_FAILED'
    $payload.blocker=$blocker
    $payload.stage_results += [ordered]@{
      name=$stage.name; task_id=$stage.task_id; status='BLOCKED'; visible_rows_before=$currentCount;
      visible_rows_after=$afterCount; browser_proof_rows=$afterProof; target_rows=[int]$stage.target;
      started_at=$started; failed_at=(Get-Date).ToUniversalTime().ToString('o'); blocker=$blocker; output_tail=$tail
    }
    Update-Queue $queuePath 'blocked' $blocker $reportRel
    $failed=$true
  }

  Write-Json $reportPath $payload
  Write-Json $resultStatusPath $payload
  if ($failed) { break }
}

$env:AAYS_PAGE_KEY=$originalPageKey
$env:AAYS_TASK_ID=$originalTaskId
$payload.current_stage=$null
$payload.completed_at=(Get-Date).ToUniversalTime().ToString('o')
$payload.final_visible_rows=Get-VisibleCount $rowsPath
$payload.final_browser_proof_rows=Get-BrowserProofCount $statusPath
if (-not $failed -and [int]$payload.final_visible_rows -eq 316 -and [int]$payload.final_browser_proof_rows -ge 316) {
  $payload.status='PASS_GAS_EMISSIONS_316_CHAIN'
  $payload.blocker=$null
} elseif (-not $payload.blocker) {
  $payload.status='BLOCKED_INCOMPLETE_CHAIN'
  $payload.blocker="Dispatcher ended before 316 verified/browser-proven rows; rows=$($payload.final_visible_rows) proof=$($payload.final_browser_proof_rows)."
}
$payload.final_ready=$false
$payload.product_final_ready=$false
$payload.fake_data=$false
Write-Json $reportPath $payload
Write-Json $resultStatusPath $payload

if ($failed) { throw $payload.blocker }
Write-Output ($payload | ConvertTo-Json -Depth 100)
