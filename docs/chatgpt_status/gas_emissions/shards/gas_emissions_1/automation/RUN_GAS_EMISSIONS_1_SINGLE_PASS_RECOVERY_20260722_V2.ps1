param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [int]$Port = 8012
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }
if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne 'gas_emissions_1') { throw 'WRONG_SLOT_CONTEXT' }
$env:AAYS_SLOT_ID = 'gas_emissions_1'
if (-not $env:AAYS_TASK_ID) { $env:AAYS_TASK_ID = 'gas_emissions_1_single_pass_recovery_20260722_01' }

$paths = [ordered]@{
  browser = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/VERIFY_100_ROWS_BROWSER_DUMP_DOM_20260722.ps1'
  hmlr = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/EXTRACT_HMLR_INSPIRE_PROXIMITY_20260722_V2.py'
  binary = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V15.py'
  classifier = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/CLASSIFY_PRTR_PI_TARGET_RECORDS_20260722_V3.py'
  semantic = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V13.py'
}
$timeouts = [ordered]@{
  browser_dump_dom = 180
  hmlr_inspire_proximity = 360
  binary_prtr_pi_parse = 1200
  classify_prtr_pi_records = 300
  semantic_annual_air_mass_gate = 300
}
$stageOutputs = [ordered]@{
  browser_dump_dom = @(
    'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_browser_dump_dom_latest.json',
    'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_browser_dump_dom_latest.json'
  )
  hmlr_inspire_proximity = @(
    'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_hmlr_inspire_proximity_latest.json',
    'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_hmlr_inspire_proximity_latest.json',
    'england_map_web/data/aays_21_slots/gas_emissions_1/hmlr_inspire_proximity_latest.json'
  )
  binary_prtr_pi_parse = @(
    'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_binary_hydration_target_parse_latest.json',
    'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_binary_hydration_target_parse_latest.json',
    'england_map_web/data/aays_21_slots/gas_emissions_1/binary_target_parse_result_latest.json'
  )
  classify_prtr_pi_records = @(
    'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_facility_emission_review_latest.json',
    'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_facility_emission_review_latest.json',
    'england_map_web/data/aays_21_slots/gas_emissions_1/facility_emission_review_latest.json'
  )
  semantic_annual_air_mass_gate = @(
    'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_facility_emission_semantic_gate_latest.json',
    'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_facility_emission_semantic_gate_latest.json',
    'england_map_web/data/aays_21_slots/gas_emissions_1/facility_emission_semantic_gate_latest.json'
  )
}
$binaryInput = 'england_map_web/data/aays_21_slots/gas_emissions_1/binary_target_parse_result_latest.json'
$classifierInput = 'england_map_web/data/aays_21_slots/gas_emissions_1/facility_emission_review_latest.json'
$reportRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_single_pass_recovery_latest.json'
$statusRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_single_pass_recovery_latest.json'
$webRel = 'england_map_web/data/aays_21_slots/gas_emissions_1/single_pass_recovery_latest.json'

function UtcNow { [DateTime]::UtcNow.ToString('o') }

function Resolve-Python {
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) { return [pscustomobject]@{ File = $python.Source; Prefix = @() } }
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) { return [pscustomobject]@{ File = $py.Source; Prefix = @('-3') } }
  return $null
}

function Tail-Text([string]$Path, [int]$Limit = 4000) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
  $text = Get-Content -LiteralPath $Path -Raw -ErrorAction SilentlyContinue
  if ($null -eq $text) { return $null }
  if ($text.Length -gt $Limit) { return $text.Substring($text.Length - $Limit) }
  return $text
}

function Stop-ProcessTree([int]$ProcessId) {
  $method = 'NONE'
  $taskkill = Get-Command taskkill.exe -ErrorAction SilentlyContinue
  if ($taskkill) {
    try {
      & $taskkill.Source /PID $ProcessId /T /F 2>$null | Out-Null
      $method = 'TASKKILL_TREE'
    }
    catch {}
  }
  try {
    $target = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($target) {
      Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
      if ($method -eq 'NONE') { $method = 'STOP_PROCESS_FALLBACK' }
    }
  }
  catch {}
  return $method
}

function Get-OutputFreshness([string[]]$RelativePaths, [DateTime]$StageStartedUtc) {
  $missing = @()
  $stale = @()
  $fresh = @()
  foreach ($relative in $RelativePaths) {
    $absolute = Join-Path $RepoRoot $relative
    if (-not (Test-Path -LiteralPath $absolute -PathType Leaf)) {
      $missing += $relative
      continue
    }
    $item = Get-Item -LiteralPath $absolute
    if ($item.Length -le 0 -or $item.LastWriteTimeUtc -lt $StageStartedUtc.AddSeconds(-2)) {
      $stale += $relative
    }
    else {
      $fresh += $relative
    }
  }
  return [pscustomobject]@{ fresh=$fresh; missing=$missing; stale=$stale; passed=(($missing.Count + $stale.Count) -eq 0) }
}

function Invoke-BoundedProcess(
  [string]$Name,
  [string]$FilePath,
  [string[]]$ArgumentList,
  [string]$RelativeScript,
  [int]$TimeoutSeconds,
  [string[]]$ExpectedOutputPaths
) {
  $startedUtc = [DateTime]::UtcNow
  $started = $startedUtc.ToString('o')
  $token = [Guid]::NewGuid().ToString('N')
  $stdout = Join-Path ([IO.Path]::GetTempPath()) ('gas_emissions_1_' + $Name + '_' + $token + '.out')
  $stderr = Join-Path ([IO.Path]::GetTempPath()) ('gas_emissions_1_' + $Name + '_' + $token + '.err')
  try {
    $process = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $RepoRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $finished = $process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $finished) {
      $termination = Stop-ProcessTree $process.Id
      try { $process.WaitForExit(10000) | Out-Null } catch {}
      $combined = ((Tail-Text $stdout) + "`n" + (Tail-Text $stderr)).Trim()
      return [pscustomobject]@{
        name=$Name; status='TIMEOUT_PROCESS_TREE_KILLED'; exit_code=124; started_at=$started; ended_at=(UtcNow)
        script=$RelativeScript; timeout_seconds=$TimeoutSeconds; blocker=('STAGE_TIMEOUT_' + $TimeoutSeconds + '_SECONDS')
        process_tree_termination=$termination; fresh_output_required=$true; output_freshness=$null; log_tail=$combined
      }
    }
    try { $process.WaitForExit() } catch {}
    $code = $process.ExitCode
    $combined = ((Tail-Text $stdout) + "`n" + (Tail-Text $stderr)).Trim()
    $freshness = Get-OutputFreshness $ExpectedOutputPaths $startedUtc
    if ($code -eq 0 -and -not $freshness.passed) {
      return [pscustomobject]@{
        name=$Name; status='BLOCKED_MISSING_OR_STALE_OUTPUT'; exit_code=125; started_at=$started; ended_at=(UtcNow)
        script=$RelativeScript; timeout_seconds=$TimeoutSeconds; blocker='EXPECTED_OUTPUT_NOT_FRESH'
        process_tree_termination='NOT_REQUIRED'; fresh_output_required=$true; output_freshness=$freshness; log_tail=$combined
      }
    }
    return [pscustomobject]@{
      name=$Name; status=$(if ($code -eq 0) {'PASS_FRESH_OUTPUTS'} else {'BLOCKED_STAGE_REPORTED'}); exit_code=$code
      started_at=$started; ended_at=(UtcNow); script=$RelativeScript; timeout_seconds=$TimeoutSeconds
      blocker=$(if ($code -eq 0) {$null} else {'NONZERO_EXIT'}); process_tree_termination='NOT_REQUIRED'
      fresh_output_required=$true; output_freshness=$freshness; log_tail=$combined
    }
  }
  catch {
    $combined = ((Tail-Text $stdout) + "`n" + (Tail-Text $stderr)).Trim()
    return [pscustomobject]@{
      name=$Name; status='STAGE_EXCEPTION'; exit_code=126; started_at=$started; ended_at=(UtcNow)
      script=$RelativeScript; timeout_seconds=$TimeoutSeconds; blocker=$_.Exception.Message
      process_tree_termination='NOT_STARTED_OR_FALLBACK'; fresh_output_required=$true; output_freshness=$null; log_tail=$combined
    }
  }
}

function Invoke-PythonStage([string]$Name, [string]$RelativeScript, [int]$TimeoutSeconds, [string]$RequiredInput = '') {
  $started = UtcNow
  $script = Join-Path $RepoRoot $RelativeScript
  if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
    return [pscustomobject]@{ name=$Name; status='MISSING_SCRIPT'; exit_code=127; started_at=$started; ended_at=(UtcNow); script=$RelativeScript; timeout_seconds=$TimeoutSeconds; blocker='SCRIPT_NOT_FOUND'; fresh_output_required=$true; output_freshness=$null; log_tail=$null }
  }
  if ($RequiredInput -and -not (Test-Path -LiteralPath (Join-Path $RepoRoot $RequiredInput) -PathType Leaf)) {
    return [pscustomobject]@{ name=$Name; status='SKIPPED_MISSING_INPUT'; exit_code=3; started_at=$started; ended_at=(UtcNow); script=$RelativeScript; timeout_seconds=$TimeoutSeconds; blocker=('MISSING_INPUT:' + $RequiredInput); fresh_output_required=$true; output_freshness=$null; log_tail=$null }
  }
  $python = Resolve-Python
  if ($null -eq $python) {
    return [pscustomobject]@{ name=$Name; status='MISSING_RUNTIME'; exit_code=127; started_at=$started; ended_at=(UtcNow); script=$RelativeScript; timeout_seconds=$TimeoutSeconds; blocker='PYTHON_OR_PY_NOT_FOUND'; fresh_output_required=$true; output_freshness=$null; log_tail=$null }
  }
  $args = @($python.Prefix) + @($script)
  return Invoke-BoundedProcess $Name $python.File $args $RelativeScript $TimeoutSeconds $stageOutputs[$Name]
}

function Test-LocalServer([string]$BaseUrl) {
  try {
    $probe = Invoke-WebRequest -UseBasicParsing -Uri ($BaseUrl + '/england_map_web/data/aays_21_slots/gas_emissions_1/browser_acceptance_100.html') -TimeoutSec 3
    return ($probe.StatusCode -ge 200 -and $probe.StatusCode -lt 400)
  }
  catch { return $false }
}

$serverProcess = $null
$serverStartedHere = $false
$serverError = $null
$orchestrationError = $null
$baseUrl = 'http://127.0.0.1:' + $Port
$stages = @()
$orchestrationStarted = UtcNow

try {
  if (-not (Test-LocalServer $baseUrl)) {
    try {
      $python = Resolve-Python
      if ($null -eq $python) {
        $serverError = 'PYTHON_OR_PY_NOT_FOUND_FOR_HTTP_SERVER'
      }
      else {
        $stdout = Join-Path ([IO.Path]::GetTempPath()) ('gas_emissions_1_http_' + [Guid]::NewGuid().ToString('N') + '.out')
        $stderr = $stdout + '.err'
        $serverArgs = @($python.Prefix) + @('-m','http.server',[string]$Port,'--bind','127.0.0.1','--directory',$RepoRoot)
        $serverProcess = Start-Process -FilePath $python.File -ArgumentList $serverArgs -WorkingDirectory $RepoRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $serverStartedHere = $true
        for ($i = 0; $i -lt 60; $i++) {
          if (Test-LocalServer $baseUrl) { break }
          if ($serverProcess.HasExited) { break }
          Start-Sleep -Milliseconds 500
        }
        if (-not (Test-LocalServer $baseUrl)) { $serverError = 'LOCAL_HTTP_SERVER_NOT_READY_WITHIN_30_SECONDS' }
      }
    }
    catch {
      $serverError = 'LOCAL_HTTP_SERVER_BOOTSTRAP_EXCEPTION:' + $_.Exception.Message
    }
  }

  $browserStarted = UtcNow
  $browserScript = Join-Path $RepoRoot $paths.browser
  if ($serverError) {
    $stages += [pscustomobject]@{ name='browser_dump_dom'; status='BLOCKED_LOCAL_HTTP_SERVER'; exit_code=3; started_at=$browserStarted; ended_at=(UtcNow); script=$paths.browser; timeout_seconds=$timeouts.browser_dump_dom; blocker=$serverError; fresh_output_required=$true; output_freshness=$null; log_tail=$null }
  }
  elseif (-not (Test-Path -LiteralPath $browserScript -PathType Leaf)) {
    $stages += [pscustomobject]@{ name='browser_dump_dom'; status='MISSING_SCRIPT'; exit_code=127; started_at=$browserStarted; ended_at=(UtcNow); script=$paths.browser; timeout_seconds=$timeouts.browser_dump_dom; blocker='SCRIPT_NOT_FOUND'; fresh_output_required=$true; output_freshness=$null; log_tail=$null }
  }
  else {
    $powershell = Get-Command powershell.exe -ErrorAction SilentlyContinue
    if (-not $powershell) { $powershell = Get-Command powershell -ErrorAction SilentlyContinue }
    if (-not $powershell) {
      $stages += [pscustomobject]@{ name='browser_dump_dom'; status='MISSING_RUNTIME'; exit_code=127; started_at=$browserStarted; ended_at=(UtcNow); script=$paths.browser; timeout_seconds=$timeouts.browser_dump_dom; blocker='POWERSHELL_CHILD_RUNTIME_NOT_FOUND'; fresh_output_required=$true; output_freshness=$null; log_tail=$null }
    }
    else {
      $browserArgs = @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$browserScript,'-RepoRoot',$RepoRoot,'-BaseUrl',$baseUrl)
      $stages += Invoke-BoundedProcess 'browser_dump_dom' $powershell.Source $browserArgs $paths.browser $timeouts.browser_dump_dom $stageOutputs.browser_dump_dom
    }
  }

  # Independent stages continue even when browser acceptance is blocked or times out.
  $stages += Invoke-PythonStage 'hmlr_inspire_proximity' $paths.hmlr $timeouts.hmlr_inspire_proximity
  $stages += Invoke-PythonStage 'binary_prtr_pi_parse' $paths.binary $timeouts.binary_prtr_pi_parse
  $stages += Invoke-PythonStage 'classify_prtr_pi_records' $paths.classifier $timeouts.classify_prtr_pi_records $binaryInput
  $stages += Invoke-PythonStage 'semantic_annual_air_mass_gate' $paths.semantic $timeouts.semantic_annual_air_mass_gate $classifierInput
}
catch {
  $orchestrationError = $_.Exception.Message
  $stages += [pscustomobject]@{ name='orchestration_exception'; status='ORCHESTRATION_EXCEPTION_RECORDED'; exit_code=126; started_at=$orchestrationStarted; ended_at=(UtcNow); script='RUN_GAS_EMISSIONS_1_SINGLE_PASS_RECOVERY_20260722_V2.ps1'; timeout_seconds=0; blocker=$orchestrationError; fresh_output_required=$false; output_freshness=$null; log_tail=$null }
}
finally {
  if ($serverStartedHere -and $serverProcess -and -not $serverProcess.HasExited) {
    Stop-ProcessTree $serverProcess.Id | Out-Null
  }
}

$passedCount = @($stages | Where-Object { $_.exit_code -eq 0 }).Count
$blockedCount = @($stages | Where-Object { $_.exit_code -ne 0 }).Count
$timedOutCount = @($stages | Where-Object { $_.status -eq 'TIMEOUT_PROCESS_TREE_KILLED' }).Count
$payload = [ordered]@{
  schema_version = 4
  architecture_version = 3
  workstream_id = 'AAYS_21_SLOT_SAFE_PARALLEL_V1'
  slot_id = 'gas_emissions_1'
  task_id = $env:AAYS_TASK_ID
  generated_at = UtcNow
  status = if ($blockedCount -eq 0) { 'PASS_SINGLE_PASS_RECOVERY_ALL_STAGES_FRESH' } elseif ($passedCount -gt 0) { 'PARTIAL_SINGLE_PASS_RECOVERY_RECORDED' } else { 'BLOCKED_SINGLE_PASS_RECOVERY_ALL_STAGES' }
  orchestration_completed = $true
  orchestration_error = $orchestrationError
  runner_execution_observed = $true
  local_http_server_started_here = $serverStartedHere
  local_http_server_error = $serverError
  browser_child_process_isolated = $true
  all_stages_hard_timeout_bounded = $true
  process_tree_termination_on_timeout = $true
  fresh_output_required_for_success = $true
  stage_timeout_seconds = $timeouts
  timeout_killed_stage_count = $timedOutCount
  stage_count = $stages.Count
  passed_stage_count = $passedCount
  blocked_stage_count = $blockedCount
  stages = $stages
  sequencing_policy = 'BROWSER_OR_TIMEOUT_FAILURE_DOES_NOT_FREEZE_OR_BLOCK_INDEPENDENT_HMLR_OR_PRTR_PI_STAGES'
  hmlr_policy = 'DEDICATED_FREEHOLD_PROXIMITY_ONLY_NO_TITLE_OR_PARCEL_ASSIGNMENT'
  parser_policy = 'V15_ADDS_S_NORTON_AND_BD_WATER_IDENTITIES_WITH_HMLR_TITLE_SEARCH_DISABLED'
  classifier_policy = 'V3_USES_EXACT_PARSER_V15_ALIAS_SET_WITH_BASE_QUALITY_GATES'
  semantic_gate_policy = 'V13_INCLUDES_V12_SURRENDER_HISTORY_AND_ADDS_HAZARDOUS_STORAGE_COOLING_WATER_FLOW_EXCLUSIONS'
  measured_facility_emission_rows_claimed_by_orchestrator = 0
  measured_parcel_emission_rows_claimed_by_orchestrator = 0
  verified_parcel_bindings_claimed_by_orchestrator = 0
  actual_business_data_rows_written_by_orchestrator = 0
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  started_at = $orchestrationStarted
  ended_at = UtcNow
}

foreach ($relative in @($reportRel,$statusRel,$webRel)) {
  $path = Join-Path $RepoRoot $relative
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
  $payload | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $path -Encoding UTF8
}
$payload | ConvertTo-Json -Depth 16
# Queue control always returns after bounded stages; stage-level JSON is authoritative.
exit 0
