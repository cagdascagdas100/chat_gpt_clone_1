param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [int]$Port = 8012,
  [int]$OverallTimeoutSeconds = 2700
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }
if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne 'gas_emissions_1') { throw 'WRONG_SLOT_CONTEXT' }
$env:AAYS_SLOT_ID = 'gas_emissions_1'
if (-not $env:AAYS_TASK_ID) { $env:AAYS_TASK_ID = 'gas_emissions_1_single_pass_recovery_20260722_01' }

$v5Rel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/RUN_GAS_EMISSIONS_1_SINGLE_PASS_RECOVERY_20260722_V5.ps1'
$v5ExpectedBlob = 'e4fa3afc3ee2961802a76421eed1e0c5944189d7'
$validationOutputs = @(
  'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_single_pass_recovery_validation_latest.json',
  'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_single_pass_recovery_validation_latest.json',
  'england_map_web/data/aays_21_slots/gas_emissions_1/single_pass_recovery_validation_latest.json'
)
$recoveryRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_single_pass_recovery_latest.json'
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

function UtcNow { [DateTime]::UtcNow.ToString('o') }

function Get-GitBlobSha([string]$Path) {
  $bytes = [IO.File]::ReadAllBytes($Path)
  $header = [Text.Encoding]::ASCII.GetBytes(('blob ' + $bytes.Length + [char]0))
  $stream = New-Object IO.MemoryStream
  try {
    $stream.Write($header, 0, $header.Length)
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Position = 0
    $sha1 = [Security.Cryptography.SHA1]::Create()
    try { return (-join ($sha1.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') })) }
    finally { $sha1.Dispose() }
  }
  finally { $stream.Dispose() }
}

function Stop-ProcessTree([int]$ProcessId) {
  $method = 'NONE'
  $taskkill = Get-Command taskkill.exe -ErrorAction SilentlyContinue
  if ($taskkill) {
    try { & $taskkill.Source /PID $ProcessId /T /F 2>$null | Out-Null; $method = 'TASKKILL_TREE' } catch {}
  }
  try {
    if (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue) {
      Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
      if ($method -eq 'NONE') { $method = 'STOP_PROCESS_FALLBACK' }
    }
  } catch {}
  return $method
}

function Read-JsonChecked([string]$RelativePath) {
  $absolute = Join-Path $RepoRoot $RelativePath
  $result = [ordered]@{ path=$RelativePath; exists=$false; nonzero=$false; json_parsed=$false; slot_id=$null; slot_ok=$false; final_ready=$null; final_ready_ok=$false; safety_ok=$false; blocker=$null }
  if (-not (Test-Path -LiteralPath $absolute -PathType Leaf)) { $result.blocker = 'FILE_NOT_FOUND'; return [pscustomobject]$result }
  $result.exists = $true
  $item = Get-Item -LiteralPath $absolute
  if ($item.Length -le 0) { $result.blocker = 'ZERO_BYTE_FILE'; return [pscustomobject]$result }
  $result.nonzero = $true
  try {
    $doc = Get-Content -LiteralPath $absolute -Raw | ConvertFrom-Json
    $result.json_parsed = $true
    $result.slot_id = [string]$doc.slot_id
    $result.slot_ok = ($result.slot_id -eq 'gas_emissions_1')
    $result.final_ready = $doc.final_ready
    $result.final_ready_ok = ($doc.final_ready -eq $false)
    $result.safety_ok = ($doc.fake_data -eq $false -and $doc.db_write -eq $false -and $doc.migration -eq $false -and $doc.production_deploy -eq $false)
    if (-not $result.slot_ok) { $result.blocker = 'WRONG_OR_MISSING_SLOT_ID' }
    elseif (-not $result.final_ready_ok) { $result.blocker = 'FINAL_READY_NOT_FALSE' }
    elseif (-not $result.safety_ok) { $result.blocker = 'SAFETY_FLAG_NOT_FALSE' }
  }
  catch { $result.blocker = 'JSON_PARSE_FAILED:' + $_.Exception.Message }
  return [pscustomobject]$result
}

function Write-Validation([object]$Payload) {
  foreach ($relative in $validationOutputs) {
    $absolute = Join-Path $RepoRoot $relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $absolute) | Out-Null
    $temp = $absolute + '.tmp.' + [Guid]::NewGuid().ToString('N')
    $Payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $temp -Encoding UTF8
    Move-Item -LiteralPath $temp -Destination $absolute -Force
  }
  $Payload | ConvertTo-Json -Depth 20
}

$startedAt = UtcNow
$childExit = 126
$timedOut = $false
$termination = 'NOT_REQUIRED'
$precheck = [ordered]@{ path=$v5Rel; expected_git_blob_sha=$v5ExpectedBlob; actual_git_blob_sha=$null; passed=$false; blocker=$null }
$checks = @()
$stageSummary = @()
$topBlockers = @()

try {
  $v5Path = Join-Path $RepoRoot $v5Rel
  if (-not (Test-Path -LiteralPath $v5Path -PathType Leaf)) { throw 'V5_CARRIER_NOT_FOUND' }
  $precheck.actual_git_blob_sha = Get-GitBlobSha $v5Path
  $precheck.passed = ($precheck.actual_git_blob_sha -eq $v5ExpectedBlob)
  if (-not $precheck.passed) { $precheck.blocker = 'V5_GIT_BLOB_SHA_MISMATCH'; throw $precheck.blocker }

  $powershell = Get-Command powershell.exe -ErrorAction SilentlyContinue
  if (-not $powershell) { $powershell = Get-Command powershell -ErrorAction SilentlyContinue }
  if (-not $powershell) { throw 'POWERSHELL_CHILD_RUNTIME_NOT_FOUND' }

  $stdout = Join-Path ([IO.Path]::GetTempPath()) ('gas_emissions_1_v6_' + [Guid]::NewGuid().ToString('N') + '.out')
  $stderr = $stdout + '.err'
  $args = @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$v5Path,'-RepoRoot',$RepoRoot,'-Port',[string]$Port)
  $process = Start-Process -FilePath $powershell.Source -ArgumentList $args -WorkingDirectory $RepoRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  $finished = $process.WaitForExit($OverallTimeoutSeconds * 1000)
  if (-not $finished) {
    $timedOut = $true
    $termination = Stop-ProcessTree $process.Id
    try { $process.WaitForExit(10000) | Out-Null } catch {}
    $childExit = 124
    $topBlockers += 'V5_OVERALL_TIMEOUT'
  }
  else {
    try { $process.WaitForExit() } catch {}
    $childExit = $process.ExitCode
    if ($childExit -ne 0) { $topBlockers += 'V5_CHILD_NONZERO_EXIT' }
  }

  $recoveryCheck = Read-JsonChecked $recoveryRel
  $checks += $recoveryCheck
  if ($recoveryCheck.blocker) { $topBlockers += ('RECOVERY_REPORT:' + $recoveryCheck.blocker) }

  $recoveryDoc = $null
  if ($recoveryCheck.json_parsed) { $recoveryDoc = Get-Content -LiteralPath (Join-Path $RepoRoot $recoveryRel) -Raw | ConvertFrom-Json }
  if ($null -ne $recoveryDoc) {
    $stageNames = @($recoveryDoc.stages | ForEach-Object { [string]$_.name })
    if ($stageNames.Count -ne 5 -or @($stageNames | Sort-Object -Unique).Count -ne 5) { $topBlockers += 'RECOVERY_STAGE_COUNT_OR_UNIQUENESS_INVALID' }
    foreach ($stage in @($recoveryDoc.stages)) {
      $name = [string]$stage.name
      $stageRow = [ordered]@{ name=$name; exit_code=$stage.exit_code; status=$stage.status; successful=($stage.exit_code -eq 0); output_checks=@(); outputs_valid=$null; blocker=$stage.blocker }
      if ($stageOutputs.Contains($name) -and $stage.exit_code -eq 0) {
        $outputChecks = @()
        foreach ($relative in $stageOutputs[$name]) {
          $check = Read-JsonChecked $relative
          $checks += $check
          $outputChecks += $check
        }
        $stageRow.output_checks = $outputChecks
        $stageRow.outputs_valid = (@($outputChecks | Where-Object { $_.blocker }).Count -eq 0)
        if (-not $stageRow.outputs_valid) { $topBlockers += ('STAGE_OUTPUT_VALIDATION_FAILED:' + $name) }
      }
      $stageSummary += [pscustomobject]$stageRow
    }
  }
}
catch {
  if (-not $precheck.blocker) { $precheck.blocker = $_.Exception.Message }
  $topBlockers += ('V6_EXCEPTION:' + $_.Exception.Message)
}

$uniqueBlockers = @($topBlockers | Where-Object { $_ } | Sort-Object -Unique)
$passed = ($precheck.passed -and -not $timedOut -and $childExit -eq 0 -and $uniqueBlockers.Count -eq 0)
$payload = [ordered]@{
  schema_version = 1
  architecture_version = 3
  workstream_id = 'AAYS_21_SLOT_SAFE_PARALLEL_V1'
  slot_id = 'gas_emissions_1'
  task_id = $env:AAYS_TASK_ID
  generated_at = UtcNow
  status = if ($passed) { 'PASS_V6_POST_RUN_JSON_AND_SAFETY_VALIDATION' } else { 'BLOCKED_V6_POST_RUN_VALIDATION_RECORDED' }
  carrier_version = 6
  wrapped_carrier_version = 5
  runner_execution_observed = $true
  overall_timeout_seconds = $OverallTimeoutSeconds
  child_exit_code = $childExit
  timed_out = $timedOut
  process_tree_termination = $termination
  git_blob_precheck = $precheck
  stage_summary = $stageSummary
  json_safety_checks = $checks
  blockers = $uniqueBlockers
  queue_control_exit_policy = 'ALWAYS_RETURN_AFTER_BOUNDED_REPORT_WRITE_STAGE_JSON_REMAINS_AUTHORITATIVE'
  measured_facility_emission_rows_claimed_by_validator = 0
  measured_parcel_emission_rows_claimed_by_validator = 0
  verified_parcel_bindings_claimed_by_validator = 0
  actual_business_data_rows_written_by_validator = 0
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  started_at = $startedAt
  ended_at = UtcNow
}
Write-Validation $payload
exit 0
