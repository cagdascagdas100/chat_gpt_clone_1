[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$expectedBranch = 'codex/aays-single-runner-v5-20260706'
$candidateRel = 'docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_candidate_join_v2_20260723.py'
$expectedCandidateBlob = 'd45ef0ad3dfccfc8ac0883f335c726c1a05fcdc3'
$outputRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json'
$gateRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/retry5_gate_latest.json'
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

if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne $slotId) { throw "WRONG_SLOT=$($env:AAYS_SLOT_ID)" }
if ($env:AAYS_TARGET_BRANCH -and $env:AAYS_TARGET_BRANCH -ne $expectedBranch) { throw "WRONG_TARGET_BRANCH=$($env:AAYS_TARGET_BRANCH)" }
if ($env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN -and $env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN.ToLowerInvariant() -ne 'true') { throw 'DIRECT_PUSH_GUARD_MISSING' }

$repoRoot = [IO.Path]::GetFullPath((Get-Location).Path).TrimEnd('\')
$candidatePath = Join-Path $repoRoot ($candidateRel -replace '/','\')
if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) { throw "PYTHON_ENTRY_MISSING=$candidatePath" }
$actualCandidateBlob = (& git -C $repoRoot hash-object -- $candidatePath 2>$null | Select-Object -First 1)
if (-not $actualCandidateBlob) { throw 'PYTHON_ENTRY_BLOB_HASH_FAILED' }
$actualCandidateBlob = ([string]$actualCandidateBlob).Trim()
if ($actualCandidateBlob -ne $expectedCandidateBlob) { throw "PYTHON_ENTRY_BLOB_MISMATCH=$actualCandidateBlob EXPECTED=$expectedCandidateBlob" }

$portableRoot = [string]$env:AAYS_PORTABLE_ROOT
if ([string]::IsNullOrWhiteSpace($portableRoot)) {
  $cursor = $repoRoot
  while ($cursor) {
    if ((Split-Path -Leaf $cursor) -eq 'runner_system') { $portableRoot = Split-Path -Parent $cursor; break }
    $parent = Split-Path -Parent $cursor
    if (-not $parent -or $parent -eq $cursor) { break }
    $cursor = $parent
  }
}

$pythonCandidates = New-Object System.Collections.Generic.List[string]
if (-not [string]::IsNullOrWhiteSpace($portableRoot)) {
  [void]$pythonCandidates.Add((Join-Path $portableRoot 'runtime\python312\python.exe'))
  [void]$pythonCandidates.Add((Join-Path $portableRoot 'runtime\python311\python.exe'))
  [void]$pythonCandidates.Add((Join-Path $portableRoot 'runtime\python\python.exe'))
}
[void]$pythonCandidates.Add((Join-Path $repoRoot '.venv\Scripts\python.exe'))
$command = Get-Command python.exe -ErrorAction SilentlyContinue
if ($command) { [void]$pythonCandidates.Add([string]$command.Source) }
$command = Get-Command python -ErrorAction SilentlyContinue
if ($command) { [void]$pythonCandidates.Add([string]$command.Source) }
$python = $pythonCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique | Select-Object -First 1
if (-not $python) { throw "PORTABLE_OR_PATH_PYTHON_NOT_AVAILABLE ROOT=$portableRoot" }

$env:AAYS_SLOT_ID = $slotId
$env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN = 'true'
& $python $candidatePath
$pythonExit = $LASTEXITCODE
if ($pythonExit -ne 0) { throw "PYTHON_ENTRY_EXIT_NONZERO=$pythonExit" }

$outputPath = Join-Path $repoRoot ($outputRel -replace '/','\')
$gatePath = Join-Path $repoRoot ($gateRel -replace '/','\')
$htmlPath = Join-Path $repoRoot ($htmlRel -replace '/','\')
if (-not (Test-Path -LiteralPath $outputPath -PathType Leaf)) { throw "CANDIDATE_OUTPUT_MISSING=$outputRel" }

try { $doc = Get-Content -LiteralPath $outputPath -Raw -Encoding UTF8 | ConvertFrom-Json }
catch { throw "CANDIDATE_OUTPUT_JSON_INVALID=$($_.Exception.Message)" }

$rows = @($doc.rows)
$ids = @($rows | ForEach-Object { [string]$_.parcel_id })
$identityOk = ($rows.Count -eq 12 -and ($ids -join '|') -eq ($expectedIds -join '|') -and (@($ids | Select-Object -Unique).Count -eq 12))
$sourceOk = ([bool]$doc.canonical_point_source.git_blob_matches_expected -and [int]$doc.canonical_point_source.actual_feature_count -eq 92283)
$urlOk = [bool]$doc.dataset_downloads.iod_2025_file7.current_v2_url_match
$joinedCount = [int]($doc.iod25_joined_candidate_rows)
$highConfidenceCount = [int]($doc.accuracy_ge_95_candidate_rows)
$businessRows = [int]($doc.actual_business_rows_written)
$rankDecileOk = (@($rows | Where-Object {
  $rank = if ($null -ne $_.iod25_crime_rank) { [int]$_.iod25_crime_rank } else { 0 }
  $decile = if ($null -ne $_.iod25_crime_decile) { [int]$_.iod25_crime_decile } else { 0 }
  $rank -lt 1 -or $rank -gt 33755 -or $decile -lt 1 -or $decile -gt 10
}).Count -eq 0)
$candidateRangeOk = (@($rows | Where-Object {
  $null -eq $_.candidate_value -or [double]$_.candidate_value -lt 0 -or [double]$_.candidate_value -gt 100
}).Count -eq 0)
$semanticsOk = (@($rows | Where-Object { [string]$_.candidate_semantics -ne $expectedSemantics }).Count -eq 0)
$businessNullOk = ($businessRows -eq 0 -and @($rows | Where-Object { $null -ne $_.business_score -or [bool]$_.promotion_allowed }).Count -eq 0)
$joinPassed = ($identityOk -and $sourceOk -and $urlOk -and $joinedCount -eq 12 -and $highConfidenceCount -eq 12 -and $rankDecileOk -and $candidateRangeOk -and $semanticsOk -and $businessNullOk)

$htmlTokenOk = $false
if (Test-Path -LiteralPath $htmlPath -PathType Leaf) {
  $html = Get-Content -LiteralPath $htmlPath -Raw -Encoding UTF8
  $htmlTokenOk = ($html.Contains('IoD25 rank') -and $html.Contains('Crime decile') -and $html.Contains('Ordinal candidate') -and $html.Contains('Business skor'))
}

$outputSha256 = (Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash.ToLowerInvariant()
$htmlSha256 = if (Test-Path -LiteralPath $htmlPath -PathType Leaf) { (Get-FileHash -LiteralPath $htmlPath -Algorithm SHA256).Hash.ToLowerInvariant() } else { $null }
$gate = [ordered]@{
  schema_version = 3
  slot_id = $slotId
  task_id = 'security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
  attempt_id = 'attempt-005'
  checked_at = [DateTimeOffset]::UtcNow.ToString('o')
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
  ui_token_gate_passed = $htmlTokenOk
  local_output_sha256 = $outputSha256
  local_html_sha256 = $htmlSha256
  served_http_hash_passed = $false
  dom_console_browser_acceptance_passed = $false
  browser_smoke_passed = $false
  post_sync_ok = $false
  manual_review_required = $true
  business_rows_written = $businessRows
  promotion_allowed = $false
  final_ready = $false
  fake_data = $false
}
Write-Utf8Atomic -Path $gatePath -Text (($gate | ConvertTo-Json -Depth 12) + "`n")

if (-not $identityOk) { throw 'CANDIDATE_OUTPUT_EXACT_TARGET_IDENTITY_FAILED' }
if (-not $businessNullOk) { throw 'BUSINESS_PROMOTION_GUARD_FAILED' }
exit 0
