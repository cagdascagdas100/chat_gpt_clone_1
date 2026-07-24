[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$taskId = 'security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId = 'attempt-005'
$expectedBranch = 'codex/aays-single-runner-v5-20260706'
$candidateRel = 'docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_candidate_join_v2_20260723.py'
$expectedCandidateBlob = 'd45ef0ad3dfccfc8ac0883f335c726c1a05fcdc3'
$outputRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json'
$candidateGateRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/retry5_candidate_gate_latest.json'
$runnerGateRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/retry5_gate_latest.json'
$htmlRel = 'england_map_web/data/aays_21_slots/security_public_safety_2/index.html'
$expectedIds = @(30762..30773 | ForEach-Object { "parcel_$_" })
$expectedSemantics = 'RELATIVE_LSOA_CRIME_DOMAIN_ORDINAL_POSITION_CANDIDATE_NOT_CARDINAL_SAFETY_SCORE'

function Write-Utf8Atomic([string]$Path,[string]$Text) {
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $tmp = "$Path.tmp.$PID.$([guid]::NewGuid().ToString('N'))"
  [IO.File]::WriteAllText($tmp,$Text,[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Sha256Bytes([byte[]]$Bytes) {
  $sha = [Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant() }
  finally { $sha.Dispose() }
}
function Sha256File([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Find-Python([string]$RepoRoot) {
  $portableRoot = [string]$env:AAYS_PORTABLE_ROOT
  if ([string]::IsNullOrWhiteSpace($portableRoot)) {
    $cursor = $RepoRoot
    while ($cursor) {
      if ((Split-Path -Leaf $cursor) -eq 'runner_system') { $portableRoot = Split-Path -Parent $cursor; break }
      $parent = Split-Path -Parent $cursor
      if (-not $parent -or $parent -eq $cursor) { break }
      $cursor = $parent
    }
  }
  $items = New-Object System.Collections.Generic.List[string]
  if (-not [string]::IsNullOrWhiteSpace($portableRoot)) {
    [void]$items.Add((Join-Path $portableRoot 'runtime\python312\python.exe'))
    [void]$items.Add((Join-Path $portableRoot 'runtime\python311\python.exe'))
    [void]$items.Add((Join-Path $portableRoot 'runtime\python\python.exe'))
  }
  [void]$items.Add((Join-Path $RepoRoot '.venv\Scripts\python.exe'))
  foreach ($name in @('python.exe','python')) { $cmd=Get-Command $name -ErrorAction SilentlyContinue; if($cmd){[void]$items.Add([string]$cmd.Source)} }
  return ($items | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique | Select-Object -First 1)
}
function Find-Browser {
  $items = New-Object System.Collections.Generic.List[string]
  foreach ($path in @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
  )) { if(-not[string]::IsNullOrWhiteSpace($path)){[void]$items.Add($path)} }
  foreach ($name in @('msedge.exe','chrome.exe')) { $cmd=Get-Command $name -ErrorAction SilentlyContinue; if($cmd){[void]$items.Add([string]$cmd.Source)} }
  return ($items | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique | Select-Object -First 1)
}
function New-FreeLoopbackPort {
  $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0)
  try { $listener.Start(); return [int]$listener.LocalEndpoint.Port }
  finally { $listener.Stop() }
}
function Stop-BoundProcess([Diagnostics.Process]$Process) {
  if ($null -eq $Process) { return }
  try { $Process.Refresh(); if(-not $Process.HasExited){Stop-Process -InputObject $Process -Force -ErrorAction Stop; $Process.WaitForExit(5000) | Out-Null} } catch {}
}
function Truncate([string]$Text,[int]$Limit=4000) { if($null-eq$Text){return''}; if($Text.Length-le$Limit){return$Text}; return $Text.Substring(0,$Limit) }

if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne $slotId) { throw "WRONG_SLOT=$($env:AAYS_SLOT_ID)" }
if ($env:AAYS_TARGET_BRANCH -and $env:AAYS_TARGET_BRANCH -ne $expectedBranch) { throw "WRONG_TARGET_BRANCH=$($env:AAYS_TARGET_BRANCH)" }
if ($env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN -and $env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN.ToLowerInvariant() -ne 'true') { throw 'DIRECT_PUSH_GUARD_MISSING' }

$repoRoot = [IO.Path]::GetFullPath((Get-Location).Path).TrimEnd('\')
$candidatePath = Join-Path $repoRoot ($candidateRel -replace '/','\')
$outputPath = Join-Path $repoRoot ($outputRel -replace '/','\')
$candidateGatePath = Join-Path $repoRoot ($candidateGateRel -replace '/','\')
$runnerGatePath = Join-Path $repoRoot ($runnerGateRel -replace '/','\')
$htmlPath = Join-Path $repoRoot ($htmlRel -replace '/','\')
if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) { throw "PYTHON_ENTRY_MISSING=$candidatePath" }
$actualCandidateBlob = (& git -C $repoRoot hash-object -- $candidatePath 2>$null | Select-Object -First 1)
if (-not $actualCandidateBlob) { throw 'PYTHON_ENTRY_BLOB_HASH_FAILED' }
$actualCandidateBlob = ([string]$actualCandidateBlob).Trim()
if ($actualCandidateBlob -ne $expectedCandidateBlob) { throw "PYTHON_ENTRY_BLOB_MISMATCH=$actualCandidateBlob EXPECTED=$expectedCandidateBlob" }
$python = Find-Python -RepoRoot $repoRoot
if (-not $python) { throw 'PORTABLE_OR_PATH_PYTHON_NOT_AVAILABLE' }

$env:AAYS_SLOT_ID = $slotId
$env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN = 'true'
& $python $candidatePath
$pythonExit = $LASTEXITCODE
if ($pythonExit -ne 0) { throw "PYTHON_ENTRY_EXIT_NONZERO=$pythonExit" }
if (-not (Test-Path -LiteralPath $outputPath -PathType Leaf)) { throw "CANDIDATE_OUTPUT_MISSING=$outputRel" }
try { $doc = Get-Content -LiteralPath $outputPath -Raw -Encoding UTF8 | ConvertFrom-Json }
catch { throw "CANDIDATE_OUTPUT_JSON_INVALID=$($_.Exception.Message)" }

$rows = @($doc.rows)
$ids = @($rows | ForEach-Object { [string]$_.parcel_id })
$identityOk = ($rows.Count -eq 12 -and ($ids -join '|') -eq ($expectedIds -join '|') -and (@($ids | Select-Object -Unique).Count -eq 12))
$sourceOk = ([bool]$doc.canonical_point_source.git_blob_matches_expected -and [int]$doc.canonical_point_source.actual_feature_count -eq 92283)
$urlOk = [bool]$doc.dataset_downloads.iod_2025_file7.current_v2_url_match
$joinedCount = [int]$doc.iod25_joined_candidate_rows
$highConfidenceCount = [int]$doc.accuracy_ge_95_candidate_rows
$businessRows = [int]$doc.actual_business_rows_written
$rankDecileOk = (@($rows | Where-Object {
  $rank = if ($null -ne $_.iod25_crime_rank) { [int]$_.iod25_crime_rank } else { 0 }
  $decile = if ($null -ne $_.iod25_crime_decile) { [int]$_.iod25_crime_decile } else { 0 }
  $rank -lt 1 -or $rank -gt 33755 -or $decile -lt 1 -or $decile -gt 10
}).Count -eq 0)
$candidateRangeOk = (@($rows | Where-Object { $null -eq $_.candidate_value -or [double]$_.candidate_value -lt 0 -or [double]$_.candidate_value -gt 100 }).Count -eq 0)
$semanticsOk = (@($rows | Where-Object { [string]$_.candidate_semantics -ne $expectedSemantics }).Count -eq 0)
$businessNullOk = ($businessRows -eq 0 -and @($rows | Where-Object { $null -ne $_.business_score -or [bool]$_.promotion_allowed }).Count -eq 0)
$joinPassed = ($identityOk -and $sourceOk -and $urlOk -and $joinedCount -eq 12 -and $highConfidenceCount -eq 12 -and $rankDecileOk -and $candidateRangeOk -and $semanticsOk -and $businessNullOk)

$htmlTokenOk = $false
if (Test-Path -LiteralPath $htmlPath -PathType Leaf) {
  $html = Get-Content -LiteralPath $htmlPath -Raw -Encoding UTF8
  $htmlTokenOk = ($html.Contains('IoD25 rank') -and $html.Contains('Crime decile') -and $html.Contains('Ordinal candidate') -and $html.Contains('Business skor'))
}
$localOutputSha256 = Sha256File -Path $outputPath
$localHtmlSha256 = if(Test-Path -LiteralPath $htmlPath -PathType Leaf){Sha256File -Path $htmlPath}else{$null}

$httpServerStarted = $false
$httpJsonStatus = 0
$httpHtmlStatus = 0
$servedJsonSha256 = $null
$servedHtmlSha256 = $null
$servedJsonHashOk = $false
$servedHtmlHashOk = $false
$browserPath = Find-Browser
$browserExitCode = -1
$browserTimedOut = $false
$domTokenOk = $false
$domExactIdsOk = $false
$consoleJavascriptErrors = @()
$browserStdout = ''
$browserStderr = ''
$server = $null
$browserProcess = $null
$serverStdout = Join-Path $env:TEMP "aays_sps2_http_$PID.stdout.log"
$serverStderr = Join-Path $env:TEMP "aays_sps2_http_$PID.stderr.log"
$browserStdoutPath = Join-Path $env:TEMP "aays_sps2_browser_$PID.stdout.log"
$browserStderrPath = Join-Path $env:TEMP "aays_sps2_browser_$PID.stderr.log"
$profileDir = Join-Path $env:TEMP "aays_sps2_browser_profile_$PID"
$httpDetail = ''
try {
  Remove-Item -LiteralPath $serverStdout,$serverStderr,$browserStdoutPath,$browserStderrPath -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $profileDir -Recurse -Force -ErrorAction SilentlyContinue
  $port = New-FreeLoopbackPort
  $baseUrl = "http://127.0.0.1:$port"
  $jsonUrl = "$baseUrl/$($outputRel -replace '\\','/' -replace '^/','')"
  $htmlUrl = "$baseUrl/$($htmlRel -replace '\\','/' -replace '^/','')"
  $server = Start-Process -FilePath $python -ArgumentList @('-m','http.server',[string]$port,'--bind','127.0.0.1','--directory',$repoRoot) -WorkingDirectory $repoRoot -RedirectStandardOutput $serverStdout -RedirectStandardError $serverStderr -PassThru -WindowStyle Hidden
  $deadline = [DateTimeOffset]::UtcNow.AddSeconds(20)
  while ([DateTimeOffset]::UtcNow -lt $deadline) {
    try { $probe = Invoke-WebRequest -UseBasicParsing -Uri $htmlUrl -TimeoutSec 3; if([int]$probe.StatusCode-eq200){$httpServerStarted=$true;break} } catch {}
    Start-Sleep -Milliseconds 500
  }
  if ($httpServerStarted) {
    $web = New-Object Net.WebClient
    try {
      $jsonBytes = $web.DownloadData($jsonUrl); $httpJsonStatus=200; $servedJsonSha256=Sha256Bytes -Bytes $jsonBytes
      $htmlBytes = $web.DownloadData($htmlUrl); $httpHtmlStatus=200; $servedHtmlSha256=Sha256Bytes -Bytes $htmlBytes
    } finally { $web.Dispose() }
    $servedJsonHashOk = ($servedJsonSha256 -eq $localOutputSha256)
    $servedHtmlHashOk = ($servedHtmlSha256 -eq $localHtmlSha256)
    if ($browserPath) {
      $args = @('--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-extensions',('--user-data-dir="{0}"' -f $profileDir),'--virtual-time-budget=3000','--dump-dom',$htmlUrl)
      $browserProcess = Start-Process -FilePath $browserPath -ArgumentList $args -WorkingDirectory $repoRoot -RedirectStandardOutput $browserStdoutPath -RedirectStandardError $browserStderrPath -PassThru -WindowStyle Hidden
      if (-not $browserProcess.WaitForExit(60000)) { $browserTimedOut=$true; Stop-BoundProcess -Process $browserProcess }
      else { $browserExitCode=[int]$browserProcess.ExitCode }
      $browserStdout = if(Test-Path -LiteralPath $browserStdoutPath){Get-Content -LiteralPath $browserStdoutPath -Raw -Encoding UTF8}else{''}
      $browserStderr = if(Test-Path -LiteralPath $browserStderrPath){Get-Content -LiteralPath $browserStderrPath -Raw -Encoding UTF8}else{''}
      $domTokenOk = ($browserStdout.Contains('IoD25 rank') -and $browserStdout.Contains('Crime decile') -and $browserStdout.Contains('Ordinal candidate') -and $browserStdout.Contains('Business skor'))
      $domExactIdsOk = (@($expectedIds | Where-Object { -not $browserStdout.Contains($_) }).Count -eq 0)
      $patterns = @('Uncaught\s+(TypeError|ReferenceError|SyntaxError|RangeError)','SEVERE:\s+javascript','Console\.error','ERR_NAME_NOT_RESOLVED','ERR_FAILED')
      foreach($pattern in $patterns){$matches=[regex]::Matches($browserStderr,$pattern,[System.Text.RegularExpressions.RegexOptions]::IgnoreCase);foreach($match in $matches){$consoleJavascriptErrors+=$match.Value}}
    }
  } else { $httpDetail='localhost static server did not become ready within 20 seconds' }
} catch { $httpDetail=$_.Exception.Message }
finally {
  Stop-BoundProcess -Process $browserProcess
  Stop-BoundProcess -Process $server
  Remove-Item -LiteralPath $profileDir -Recurse -Force -ErrorAction SilentlyContinue
}
$consoleOk = ($consoleJavascriptErrors.Count -eq 0)
$browserPassed = ($joinPassed -and $htmlTokenOk -and $httpServerStarted -and $httpJsonStatus -eq 200 -and $httpHtmlStatus -eq 200 -and $servedJsonHashOk -and $servedHtmlHashOk -and $browserPath -and -not $browserTimedOut -and $browserExitCode -eq 0 -and $domTokenOk -and $domExactIdsOk -and $consoleOk)
$checkedAt = [DateTimeOffset]::UtcNow.ToString('o')
$gate = [ordered]@{
  schema_version = 4
  slot_id = $slotId
  task_id = $taskId
  attempt_id = $attemptId
  checked_at = $checkedAt
  candidate_entry_blob_sha = $expectedCandidateBlob
  exact_target_ids_passed = $identityOk
  canonical_point_blob_and_feature_count_passed = $sourceOk
  current_v2_iod25_final_url_passed = $urlOk
  iod25_joined_candidate_rows = $joinedCount
  accuracy_ge_95_candidate_rows = $highConfidenceCount
  rank_decile_range_passed = $rankDecileOk
  candidate_range_passed = $candidateRangeOk
  candidate_semantics_passed = $semanticsOk
  business_rows_zero_and_promotion_closed = $businessNullOk
  candidate_join_passed = $joinPassed
  source_row_gate_passed = $joinPassed
  local_output_sha256 = $localOutputSha256
  local_html_sha256 = $localHtmlSha256
  localhost_server_started = $httpServerStarted
  http_json_status = $httpJsonStatus
  http_html_status = $httpHtmlStatus
  served_json_sha256 = $servedJsonSha256
  served_html_sha256 = $servedHtmlSha256
  served_json_hash_passed = $servedJsonHashOk
  served_html_hash_passed = $servedHtmlHashOk
  served_http_hash_passed = ($servedJsonHashOk -and $servedHtmlHashOk)
  browser_executable = $browserPath
  browser_exit_code = $browserExitCode
  browser_timed_out = $browserTimedOut
  dom_required_tokens_passed = $domTokenOk
  dom_exact_target_ids_passed = $domExactIdsOk
  console_javascript_error_count = $consoleJavascriptErrors.Count
  console_javascript_errors = @($consoleJavascriptErrors | Select-Object -Unique)
  console_acceptance_passed = $consoleOk
  ui_token_gate_passed = ($htmlTokenOk -and $domTokenOk -and $domExactIdsOk)
  dom_console_browser_acceptance_passed = $browserPassed
  browser_smoke_passed = $browserPassed
  post_sync_ok = $false
  manual_review_required = (-not $browserPassed)
  business_rows_written = $businessRows
  promotion_allowed = $false
  final_ready = $false
  fake_data = $false
  http_detail = $httpDetail
  browser_stdout_excerpt = Truncate -Text $browserStdout
  browser_stderr_excerpt = Truncate -Text $browserStderr
}
$gateText = (($gate | ConvertTo-Json -Depth 16) + "`n")
Write-Utf8Atomic -Path $candidateGatePath -Text $gateText
Write-Utf8Atomic -Path $runnerGatePath -Text $gateText

Remove-Item -LiteralPath $serverStdout,$serverStderr,$browserStdoutPath,$browserStderrPath -Force -ErrorAction SilentlyContinue
if (-not $identityOk) { Write-Error 'CANDIDATE_OUTPUT_EXACT_TARGET_IDENTITY_FAILED'; exit 31 }
if (-not $businessNullOk) { Write-Error 'BUSINESS_PROMOTION_GUARD_FAILED'; exit 32 }
if (-not $joinPassed) { Write-Error 'CANDIDATE_JOIN_GATE_FAILED'; exit 41 }
if (-not $browserPassed) { Write-Error 'SERVED_HTTP_DOM_CONSOLE_BROWSER_ACCEPTANCE_FAILED'; exit 42 }
exit 0
