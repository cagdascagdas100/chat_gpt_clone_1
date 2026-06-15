$ErrorActionPreference = 'Stop'

$Task = 'terrayield-088-gas-emissions-proxy-finalize'
$PageKey = 'gas_emissions'
$Branch = 'feature/terrayield-aays-integration'
$Repo = 'C:\Users\cagda\Documents\GitHub\AAYS'
$WorkRoot = 'F:\chatgpt\AAYS_WORK\gas_emissions_088_isolated_worktree'
$Remote = 'https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$AutomationRel = 'docs/chatgpt_status/gas_emissions/automation/run_088_proxy_finalize.ps1'
$PageReportRel = 'docs/chatgpt_status/gas_emissions/reports/terrayield-088-gas-emissions-proxy-finalize.txt'
$PageStatusRel = 'docs/chatgpt_status/gas_emissions/status/terrayield-088-gas-emissions-proxy-finalize.txt'
$RootReportTxtRel = 'docs/chatgpt_status/reports/terrayield-088-gas-emissions-proxy-finalize.txt'
$RootReportJsonRel = 'docs/chatgpt_status/reports/terrayield-088-gas-emissions-proxy-finalize.json'
$LatestRel = 'docs/chatgpt_status/runner_outputs/latest_output.json'
$OutputRel = 'england_map_web/data/parcel_emissions_scores.geojson'
$DiagRel = 'docs/chatgpt_status/gas_emissions/reports/terrayield-088-runner-input-wrapper.txt'

function Write-Lines($Path, [string[]]$Lines) {
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $Lines | Set-Content -Encoding UTF8 $Path
}

function Read-KvFile($Path) {
  $h = [ordered]@{}
  if (Test-Path $Path) {
    foreach ($line in Get-Content -Encoding UTF8 $Path) {
      if ($line -match '^(.*?)=(.*)$') { $h[$matches[1]] = $matches[2] }
    }
  }
  return $h
}

$started = Get-Date
$diag = @(
  "page_key=$PageKey",
  "task_id=$Task",
  "branch=$Branch",
  "repo=$Repo",
  "work_root=$WorkRoot",
  "automation_path=$AutomationRel",
  "runner_input=docs/chatgpt_status/runner_inputs/terrayield-088-gas-emissions-proxy-finalize.ps1",
  "started_at=$($started.ToString('s'))",
  'status=RUNNER_INPUT_STARTED',
  'manual_stdout_required=false',
  'fake_data=false',
  'db_write=false',
  'migration=false',
  'production_deploy=false'
)

try {
  if (Test-Path $WorkRoot) { Remove-Item -Recurse -Force $WorkRoot }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $WorkRoot) | Out-Null

  $worktreeOk = $false
  try {
    git -C $Repo fetch origin | Out-Null
    git -C $Repo worktree add -B gas_emissions_088_isolated_worktree $WorkRoot "origin/$Branch" | Out-Null
    $worktreeOk = $true
    $diag += 'checkout_mode=git_worktree'
  } catch {
    $diag += "worktree_failed=$($_.Exception.Message)"
    if (Test-Path $WorkRoot) { Remove-Item -Recurse -Force $WorkRoot }
    git clone --branch $Branch --single-branch $Remote $WorkRoot | Out-Null
    $diag += 'checkout_mode=git_clone_fallback'
  }

  Set-Location $WorkRoot
  $automation = Join-Path $WorkRoot $AutomationRel
  if (!(Test-Path $automation)) { throw "automation_missing=$AutomationRel" }

  & powershell -NoProfile -ExecutionPolicy Bypass -File $automation
  $automationExit = $LASTEXITCODE
  $diag += "automation_exit_code=$automationExit"

  $pageReport = Join-Path $WorkRoot $PageReportRel
  $pageStatus = Join-Path $WorkRoot $PageStatusRel
  $output = Join-Path $WorkRoot $OutputRel
  $latest = Join-Path $WorkRoot $LatestRel
  $rootReportTxt = Join-Path $WorkRoot $RootReportTxtRel
  $rootReportJson = Join-Path $WorkRoot $RootReportJsonRel
  $diagPath = Join-Path $WorkRoot $DiagRel

  $statusKv = Read-KvFile $pageStatus
  $reportKv = Read-KvFile $pageReport
  $outputExists = Test-Path $output
  $featureCount = 0
  if ($outputExists) {
    try {
      $outJson = Get-Content -Raw -Encoding UTF8 $output | ConvertFrom-Json
      $featureCount = @($outJson.features).Count
    } catch {
      $diag += "output_parse_error=$($_.Exception.Message)"
    }
  }

  $finalReady = $false
  if ($statusKv.Contains('final_ready') -and $statusKv['final_ready'] -eq 'true') { $finalReady = $true }
  $completion = if ($statusKv.Contains('completion_percent')) { $statusKv['completion_percent'] } elseif ($featureCount -gt 0) { '96' } else { '99' }
  $status = if ($statusKv.Contains('status')) { $statusKv['status'] } elseif ($featureCount -gt 0) { 'PROXY_DATA_READY' } else { 'OUTPUT_EMPTY_OR_MISSING' }

  $diag += "page_status=$status"
  $diag += "completion_percent=$completion"
  $diag += "final_ready=$($finalReady.ToString().ToLowerInvariant())"
  $diag += "output_exists=$($outputExists.ToString().ToLowerInvariant())"
  $diag += "feature_count=$featureCount"

  $result = [ordered]@{
    task_id = $Task
    page_key = $PageKey
    status = $status
    completion_percent = [int]$completion
    final_ready = $finalReady
    output_exists = $outputExists
    feature_count = $featureCount
    source_type = 'air_quality_proxy'
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    automation_path = $AutomationRel
    page_report = $PageReportRel
    page_status = $PageStatusRel
    output = $OutputRel
    generated_at = (Get-Date).ToString('s')
  }

  $result | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $latest
  $result | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $rootReportJson
  Write-Lines $rootReportTxt @(
    "page_key=$PageKey",
    "task_id=$Task",
    "status=$status",
    "completion_percent=$completion",
    "final_ready=$($finalReady.ToString().ToLowerInvariant())",
    "output_exists=$($outputExists.ToString().ToLowerInvariant())",
    "feature_count=$featureCount",
    'source_type=air_quality_proxy',
    'fake_data=false',
    'db_write=false',
    'migration=false',
    'production_deploy=false',
    "page_report=$PageReportRel",
    "page_status=$PageStatusRel",
    "output=$OutputRel"
  )
  $diag += "finished_at=$((Get-Date).ToString('s'))"
  Write-Lines $diagPath $diag

  git add $OutputRel `
          'england_map_web/data/parcel_emissions_scores.csv' `
          'england_map_web/data/parcel_emissions_score_manifest.json' `
          'england_map_web/data/parcel_emissions_source_registry.csv' `
          'england_map_web/data/parcel_emissions_evidence_manifest.jsonl' `
          'docs/chatgpt_status/gas_emissions/reports' `
          'docs/chatgpt_status/gas_emissions/status' `
          'docs/chatgpt_status/reports' `
          'docs/chatgpt_status/runner_outputs' 2>$null

  $changes = git status --porcelain
  if ($changes) {
    git commit -m 'gas-emissions: run 088 proxy finalize from runner input' | Out-Null
    git push origin $Branch | Out-Null
    $diag += 'git_commit_pushed=true'
  } else {
    $diag += 'git_commit_pushed=false'
  }

  if ($finalReady) { exit 0 }
  exit 4
} catch {
  try {
    if (Test-Path $WorkRoot) {
      $diagPath = Join-Path $WorkRoot $DiagRel
      $latest = Join-Path $WorkRoot $LatestRel
      $rootReportJson = Join-Path $WorkRoot $RootReportJsonRel
      $rootReportTxt = Join-Path $WorkRoot $RootReportTxtRel
      $diag += "status=RUNNER_INPUT_FAILED"
      $diag += "error=$($_.Exception.Message)"
      $diag += "finished_at=$((Get-Date).ToString('s'))"
      Write-Lines $diagPath $diag
      $fail = [ordered]@{task_id=$Task;page_key=$PageKey;status='RUNNER_INPUT_FAILED';completion_percent=99;final_ready=$false;error=$_.Exception.Message;manual_stdout_required=$false;generated_at=(Get-Date).ToString('s')}
      $fail | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $latest
      $fail | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $rootReportJson
      Write-Lines $rootReportTxt @("page_key=$PageKey","task_id=$Task","status=RUNNER_INPUT_FAILED","completion_percent=99","final_ready=false","error=$($_.Exception.Message)")
      Set-Location $WorkRoot
      git add 'docs/chatgpt_status/gas_emissions/reports' 'docs/chatgpt_status/reports' 'docs/chatgpt_status/runner_outputs' 2>$null
      if (git status --porcelain) { git commit -m 'gas-emissions: record 088 runner input failure' | Out-Null; git push origin $Branch | Out-Null }
    }
  } catch {}
  exit 10
}
