[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$taskId = 'security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId = 'attempt-005'
$v3Rel = 'docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_browser_gate_bridge_v3_20260723.ps1'
$expectedV3Blob = '896f820b09b8442f3172df12fe3bfda28bb17347'
$outputRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json'
$candidateGateRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/retry5_candidate_gate_latest.json'
$runnerGateRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/retry5_gate_latest.json'
$htmlRel = 'england_map_web/data/aays_21_slots/security_public_safety_2/index.html'
$expectedIds = @(30762..30773 | ForEach-Object { "parcel_$_" })

function Write-Utf8Atomic([string]$Path,[string]$Text) {
  $dir=Split-Path -Parent $Path
  if(-not(Test-Path -LiteralPath $dir)){New-Item -ItemType Directory -Force -Path $dir|Out-Null}
  $tmp="$Path.tmp.$PID.$([guid]::NewGuid().ToString('N'))"
  [IO.File]::WriteAllText($tmp,$Text,[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function GitBlob([string]$Path) {
  if(-not(Test-Path -LiteralPath $Path -PathType Leaf)){return$null}
  $value=(& git -C (Get-Location).Path hash-object -- $Path 2>$null|Select-Object -First 1)
  if(-not$value){return$null};return([string]$value).Trim()
}
function Read-Json([string]$Path) {
  if(-not(Test-Path -LiteralPath $Path -PathType Leaf)){return$null}
  try{return(Get-Content -LiteralPath $Path -Raw -Encoding UTF8|ConvertFrom-Json)}catch{return$null}
}
function Set-Field([object]$Object,[string]$Name,[object]$Value) {
  Add-Member -InputObject $Object -NotePropertyName $Name -NotePropertyValue $Value -Force
}

if($env:AAYS_SLOT_ID-and$env:AAYS_SLOT_ID-ne$slotId){throw"WRONG_SLOT=$($env:AAYS_SLOT_ID)"}
$repoRoot=[IO.Path]::GetFullPath((Get-Location).Path).TrimEnd('\')
$v3Path=Join-Path $repoRoot ($v3Rel-replace'/','\')
$outputPath=Join-Path $repoRoot ($outputRel-replace'/','\')
$candidateGatePath=Join-Path $repoRoot ($candidateGateRel-replace'/','\')
$runnerGatePath=Join-Path $repoRoot ($runnerGateRel-replace'/','\')
$htmlPath=Join-Path $repoRoot ($htmlRel-replace'/','\')
$actualV3Blob=GitBlob -Path $v3Path
if($actualV3Blob-ne$expectedV3Blob){throw"BROWSER_GATE_V3_BLOB_MISMATCH=$actualV3Blob EXPECTED=$expectedV3Blob"}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $v3Path
$v3Exit=$LASTEXITCODE
if($null-eq$v3Exit){$v3Exit=1}
if($v3Exit-notin@(0,42)){exit $v3Exit}

$doc=Read-Json -Path $outputPath
$gate=Read-Json -Path $candidateGatePath
if($null-eq$doc-or$null-eq$gate){Write-Error 'V3_OUTPUT_OR_CANDIDATE_GATE_MISSING_OR_INVALID';exit 51}
if(-not(Test-Path -LiteralPath $htmlPath -PathType Leaf)){Write-Error 'GENERATED_HTML_MISSING';exit 52}
$html=Get-Content -LiteralPath $htmlPath -Raw -Encoding UTF8
$rows=@($doc.rows)
$jsonIds=@($rows|ForEach-Object{[string]$_.parcel_id})
$jsonIdentityOk=($rows.Count-eq12-and($jsonIds-join'|')-eq($expectedIds-join'|')-and@($jsonIds|Select-Object -Unique).Count-eq12)

$localCellMatches=[regex]::Matches($html,'<td>\s*(parcel_\d+)\s*</td>',[Text.RegularExpressions.RegexOptions]::IgnoreCase)
$localCellIds=@($localCellMatches|ForEach-Object{$_.Groups[1].Value.ToLowerInvariant()})
$localTargetCells=@($localCellIds|Where-Object{$expectedIds-contains$_})
$localExactTableRowsOk=($localTargetCells.Count-eq12-and($localTargetCells-join'|')-eq($expectedIds-join'|')-and@($localTargetCells|Select-Object -Unique).Count-eq12)

$scriptTagCount=[regex]::Matches($html,'<script\b',[Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
$inlineHandlerCount=[regex]::Matches($html,'\son[a-z][a-z0-9_-]*\s*=',[Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
$javascriptUrlCount=[regex]::Matches($html,'javascript\s*:',[Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
$executableJsSurfaceAbsent=($scriptTagCount-eq0-and$inlineHandlerCount-eq0-and$javascriptUrlCount-eq0)

$domText=[string]$gate.browser_stdout_excerpt
$domCellMatches=[regex]::Matches($domText,'<td>\s*(parcel_\d+)\s*</td>',[Text.RegularExpressions.RegexOptions]::IgnoreCase)
$domCellIds=@($domCellMatches|ForEach-Object{$_.Groups[1].Value.ToLowerInvariant()})
$domTargetCells=@($domCellIds|Where-Object{$expectedIds-contains$_})
$domExactTableRowsFromExcerptOk=($domTargetCells.Count-eq12-and($domTargetCells-join'|')-eq($expectedIds-join'|')-and@($domTargetCells|Select-Object -Unique).Count-eq12)
$domIdentityEvidenceOk=([bool]$gate.dom_exact_target_ids_passed-and([bool]$domExactTableRowsFromExcerptOk-or[bool]$gate.dom_required_tokens_passed))

$baseBrowserOk=(
  [bool]$gate.candidate_join_passed -and
  [bool]$gate.served_json_hash_passed -and
  [bool]$gate.served_html_hash_passed -and
  -not[bool]$gate.browser_timed_out -and
  [int]$gate.browser_exit_code-eq0 -and
  [bool]$gate.dom_required_tokens_passed -and
  [bool]$gate.dom_exact_target_ids_passed
)
$staticConsoleAcceptanceOk=($executableJsSurfaceAbsent-and$baseBrowserOk)
$browserPassed=($jsonIdentityOk-and$localExactTableRowsOk-and$staticConsoleAcceptanceOk-and$domIdentityEvidenceOk)

Set-Field $gate 'schema_version' 5
Set-Field $gate 'browser_gate_version' 'v4-static-no-js-exact-table'
Set-Field $gate 'v3_exit_code' ([int]$v3Exit)
Set-Field $gate 'json_exact_target_identity_passed' $jsonIdentityOk
Set-Field $gate 'local_html_exact_twelve_table_rows_passed' $localExactTableRowsOk
Set-Field $gate 'local_html_target_table_ids' @($localTargetCells)
Set-Field $gate 'executable_javascript_surface' ([ordered]@{script_tag_count=$scriptTagCount;inline_event_handler_count=$inlineHandlerCount;javascript_url_count=$javascriptUrlCount;absent=$executableJsSurfaceAbsent})
Set-Field $gate 'dom_exact_table_rows_from_excerpt_passed' $domExactTableRowsFromExcerptOk
Set-Field $gate 'dom_target_table_ids_from_excerpt' @($domTargetCells)
Set-Field $gate 'console_acceptance_basis' 'served_html_sha256_equals_local_plus_static_no_script_no_inline_handler_no_javascript_url_plus_successful_headless_serialized_dom'
Set-Field $gate 'console_acceptance_passed' $staticConsoleAcceptanceOk
Set-Field $gate 'dom_console_browser_acceptance_passed' $browserPassed
Set-Field $gate 'browser_smoke_passed' $browserPassed
Set-Field $gate 'manual_review_required' (-not$browserPassed)
Set-Field $gate 'post_sync_ok' $null
Set-Field $gate 'post_sync_verification_external_to_automation' $true
Set-Field $gate 'final_ready' $false
Set-Field $gate 'fake_data' $false
$text=(($gate|ConvertTo-Json -Depth 18)+"`n")
Write-Utf8Atomic -Path $candidateGatePath -Text $text
Write-Utf8Atomic -Path $runnerGatePath -Text $text

if(-not$jsonIdentityOk){Write-Error 'V4_JSON_EXACT_TARGET_IDENTITY_FAILED';exit 53}
if(-not$localExactTableRowsOk){Write-Error 'V4_LOCAL_HTML_EXACT_TABLE_ROWS_FAILED';exit 54}
if(-not$executableJsSurfaceAbsent){Write-Error 'V4_EXECUTABLE_JAVASCRIPT_SURFACE_PRESENT_REQUIRES_CDP_CONSOLE_CAPTURE';exit 55}
if(-not$browserPassed){Write-Error 'V4_FAIL_CLOSED_SERVED_STATIC_HTML_DOM_ACCEPTANCE_FAILED';exit 56}
exit 0
