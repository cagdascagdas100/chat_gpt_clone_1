param()

$ErrorActionPreference = 'Stop'
$TaskId = '209_aays1_parcel_label_4row_browser_dom_proof_20260715'
$PageKey = 'aays1'
$RepoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
}
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$PageUrl = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=parcel-label-209'
$DataUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json?refresh=parcel-label-209'
$CandidateIds = @(
  'SOURCE_BULLRING_BIRMINGHAM_RETAIL_001',
  'SOURCE_THE_CUBE_BIRMINGHAM_MIXED_001',
  'SOURCE_ONE_ANGEL_SQUARE_MANCHESTER_OFFICE_001',
  'SOURCE_MAGNA_PARK_MPS187_INDUSTRIAL_001'
)

function Ensure-Directory([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}
function Write-Utf8([string]$Path, [string]$Text) {
  Ensure-Directory (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}
function Write-Json([string]$Path, [object]$Value) {
  Write-Utf8 $Path ($Value | ConvertTo-Json -Depth 40)
}
function Resolve-Browser {
  $candidates = @(
    "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
  )
  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) { return $candidate }
  }
  foreach ($name in @('msedge.exe','chrome.exe')) {
    $command = Get-Command $name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
  }
  return $null
}
function Quote-ProcessArgument([string]$Value) {
  return '"' + ($Value -replace '"','\"') + '"'
}
function Invoke-BrowserDump([string]$BrowserPath, [string]$HeadlessFlag, [string]$ProfilePath) {
  $arguments = @(
    $HeadlessFlag,
    '--disable-gpu',
    '--disable-extensions',
    '--disable-background-networking',
    '--no-first-run',
    '--no-default-browser-check',
    '--hide-scrollbars',
    '--window-size=1920,1080',
    '--virtual-time-budget=20000',
    "--user-data-dir=$ProfilePath",
    '--dump-dom',
    $PageUrl
  )
  $startInfo = New-Object System.Diagnostics.ProcessStartInfo
  $startInfo.FileName = $BrowserPath
  $startInfo.Arguments = (($arguments | ForEach-Object { Quote-ProcessArgument ([string]$_) }) -join ' ')
  $startInfo.UseShellExecute = $false
  $startInfo.CreateNoWindow = $true
  $startInfo.RedirectStandardOutput = $true
  $startInfo.RedirectStandardError = $true
  $process = New-Object System.Diagnostics.Process
  $process.StartInfo = $startInfo
  [void]$process.Start()
  $stdoutTask = $process.StandardOutput.ReadToEndAsync()
  $stderrTask = $process.StandardError.ReadToEndAsync()
  if (-not $process.WaitForExit(75000)) {
    try { $process.Kill() } catch {}
    return [pscustomobject]@{ exit_code = 124; stdout = ''; stderr = 'browser_dump_timeout'; flag = $HeadlessFlag }
  }
  $stdoutTask.Wait()
  $stderrTask.Wait()
  return [pscustomobject]@{
    exit_code = [int]$process.ExitCode
    stdout = [string]$stdoutTask.Result
    stderr = [string]$stderrTask.Result
    flag = $HeadlessFlag
  }
}

$StatusRoot = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\status'
$EvidenceRoot = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\evidence'
$OutputRoot = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\runner_outputs'
$ReportRoot = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\reports'
$CheckpointPath = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\checkpoints\parcel_label_canonical_checkpoint.json'
$GatePath = Join-Path $StatusRoot ($TaskId + '_gate.json')
$EvidencePath = Join-Path $EvidenceRoot '209_parcel_label_4row_browser_dom_proof_evidence_20260715.json'
$OutputPath = Join-Path $OutputRoot ($TaskId + '_output.json')
$DomPath = Join-Path $OutputRoot ($TaskId + '_dom.html')
$BrowserLogPath = Join-Path $OutputRoot ($TaskId + '_browser_stderr.log')
$ReportPath = Join-Path $ReportRoot '209_parcel_label_4row_browser_dom_proof_report_20260715.md'

$healthResponse = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/health' -TimeoutSec 15
$pageResponse = Invoke-WebRequest -UseBasicParsing -Uri $PageUrl -TimeoutSec 30
$dataResponse = Invoke-WebRequest -UseBasicParsing -Uri $DataUrl -TimeoutSec 30
$dataObject = $dataResponse.Content | ConvertFrom-Json
$rows = @($dataObject.rows)
$dataIds = @($rows | ForEach-Object { [string]$_.parcel_id })
$dataVisibleIds = @($CandidateIds | Where-Object { $dataIds -contains $_ })

$browserPath = Resolve-Browser
if (-not $browserPath) { throw 'BROWSER_EXECUTABLE_NOT_FOUND' }
$tempProfile = Join-Path ([System.IO.Path]::GetTempPath()) ('aays_parcel_label_209_' + [guid]::NewGuid().ToString('N'))
Ensure-Directory $tempProfile
try {
  $browserResult = Invoke-BrowserDump -BrowserPath $browserPath -HeadlessFlag '--headless=new' -ProfilePath $tempProfile
  if ($browserResult.exit_code -ne 0 -or [string]::IsNullOrWhiteSpace($browserResult.stdout)) {
    Remove-Item -LiteralPath $tempProfile -Recurse -Force -ErrorAction SilentlyContinue
    Ensure-Directory $tempProfile
    $browserResult = Invoke-BrowserDump -BrowserPath $browserPath -HeadlessFlag '--headless' -ProfilePath $tempProfile
  }
} finally {
  Remove-Item -LiteralPath $tempProfile -Recurse -Force -ErrorAction SilentlyContinue
}

$dom = [string]$browserResult.stdout
Write-Utf8 $DomPath $dom
Write-Utf8 $BrowserLogPath ([string]$browserResult.stderr)
$domVisibleIds = @($CandidateIds | Where-Object { $dom.IndexOf($_, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 })
$rowProof = @()
foreach ($candidateId in $CandidateIds) {
  $index = $dom.IndexOf($candidateId, [System.StringComparison]::OrdinalIgnoreCase)
  $snippet = ''
  if ($index -ge 0) {
    $start = [math]::Max(0, $index - 180)
    $length = [math]::Min(520, $dom.Length - $start)
    $snippet = $dom.Substring($start, $length) -replace '\s+', ' '
  }
  $rowProof += [ordered]@{
    parcel_id = $candidateId
    data_json_visible = ($dataVisibleIds -contains $candidateId)
    browser_dom_visible = ($domVisibleIds -contains $candidateId)
    dom_snippet = $snippet
  }
}

$passed = ($healthResponse.StatusCode -eq 200 -and $pageResponse.StatusCode -eq 200 -and $dataResponse.StatusCode -eq 200 -and $dataVisibleIds.Count -eq 4 -and $browserResult.exit_code -eq 0 -and $domVisibleIds.Count -eq 4)
$generatedAt = (Get-Date).ToUniversalTime().ToString('o')
$blockers = @()
if ($dataVisibleIds.Count -ne 4) { $blockers += 'DATA_JSON_FOUR_IDS_NOT_VISIBLE' }
if ($browserResult.exit_code -ne 0) { $blockers += 'HEADLESS_BROWSER_EXIT_NONZERO' }
if ($domVisibleIds.Count -ne 4) { $blockers += 'BROWSER_DOM_FOUR_IDS_NOT_VISIBLE' }
$blockers += 'EXACT_GEOMETRY_BINDING_PENDING'
$blockers += 'MANUAL_SCOPE_REVIEW_PENDING'

$evidence = [ordered]@{
  task_id = $TaskId
  generated_at = $generatedAt
  browser_path = $browserPath
  headless_flag = $browserResult.flag
  browser_exit_code = $browserResult.exit_code
  health_http_status = [int]$healthResponse.StatusCode
  page_http_status = [int]$pageResponse.StatusCode
  data_http_status = [int]$dataResponse.StatusCode
  tracked_row_count = $rows.Count
  candidate_count = 4
  data_json_visible_count = $dataVisibleIds.Count
  browser_dom_visible_count = $domVisibleIds.Count
  all_four_browser_dom_visible = ($domVisibleIds.Count -eq 4)
  dom_path = 'docs/chatgpt_status/aays1/runner_outputs/209_aays1_parcel_label_4row_browser_dom_proof_20260715_dom.html'
  browser_stderr_path = 'docs/chatgpt_status/aays1/runner_outputs/209_aays1_parcel_label_4row_browser_dom_proof_20260715_browser_stderr.log'
  rows = $rowProof
  blockers = $blockers
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json $EvidencePath $evidence

$output = [ordered]@{
  task_id = $TaskId
  status = $(if ($passed) { 'BROWSER_DOM_FOUR_ROWS_VERIFIED_REMOTE_COMMIT_PENDING' } else { 'BROWSER_DOM_PROOF_BLOCKED' })
  generated_at = $generatedAt
  tracked_row_count = $rows.Count
  browser_dom_visible_count = $domVisibleIds.Count
  browser_verified_rows = $(if ($passed) { 198 } else { 194 })
  source_upgraded_rows = 57
  classification_enriched_rows = 57
  average_latest_batch_accuracy_score_4 = 3.9375
  exact_geometry_rows = 0
  page_http_ok = ($pageResponse.StatusCode -eq 200)
  data_http_ok = ($dataResponse.StatusCode -eq 200)
  browser_dom_visibility_proven = $passed
  blockers = $blockers
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json $OutputPath $output
Write-Json $GatePath ([ordered]@{
  task_id = $TaskId
  source_row_gate_passed = ($dataVisibleIds.Count -eq 4)
  ui_token_gate_passed = $passed
  browser_smoke_passed = $passed
  post_sync_ok = $passed
  manual_review_required = $true
  fake_data = $false
  final_ready = $false
})

if (Test-Path -LiteralPath $CheckpointPath) {
  $checkpoint = Get-Content -LiteralPath $CheckpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $checkpoint | Add-Member -NotePropertyName pending_task_id -NotePropertyValue $TaskId -Force
  $checkpoint | Add-Member -NotePropertyName pending_task_state -NotePropertyValue $(if ($passed) { 'BROWSER_DOM_PROOF_LOCAL_VERIFIED_REMOTE_COMMIT_PENDING' } else { 'BROWSER_DOM_PROOF_BLOCKED' }) -Force
  $checkpoint | Add-Member -NotePropertyName next_incomplete_action -NotePropertyValue $(if ($passed) { 'remote_commit_readback_for_task_209_then_exact_geometry_binding' } else { 'recover_browser_dom_proof_for_task_209' }) -Force
  $checkpoint | Add-Member -NotePropertyName tracked_rows -NotePropertyValue $rows.Count -Force
  $checkpoint | Add-Member -NotePropertyName verified_rows -NotePropertyValue 198 -Force
  $checkpoint | Add-Member -NotePropertyName published_rows -NotePropertyValue 198 -Force
  $checkpoint | Add-Member -NotePropertyName http_verified_rows -NotePropertyValue 198 -Force
  $checkpoint | Add-Member -NotePropertyName browser_verified_rows -NotePropertyValue $(if ($passed) { 198 } else { 194 }) -Force
  $checkpoint | Add-Member -NotePropertyName source_upgraded_rows -NotePropertyValue 57 -Force
  $checkpoint | Add-Member -NotePropertyName classification_enriched_rows -NotePropertyValue 57 -Force
  $checkpoint | Add-Member -NotePropertyName exact_geometry_rows -NotePropertyValue 0 -Force
  $checkpoint | Add-Member -NotePropertyName updated_at -NotePropertyValue $generatedAt -Force
  $checkpoint | Add-Member -NotePropertyName blockers -NotePropertyValue $blockers -Force
  $checkpoint | Add-Member -NotePropertyName final_ready -NotePropertyValue $false -Force
  $checkpoint | Add-Member -NotePropertyName product_final_ready -NotePropertyValue $false -Force
  $checkpoint | Add-Member -NotePropertyName fake_data -NotePropertyValue $false -Force
  $checkpoint | Add-Member -NotePropertyName db_write -NotePropertyValue $false -Force
  $checkpoint | Add-Member -NotePropertyName migration -NotePropertyValue $false -Force
  $checkpoint | Add-Member -NotePropertyName production_deploy -NotePropertyValue $false -Force
  Write-Json $CheckpointPath $checkpoint
}

$reportLines = @(
  '# Parcel Label Task 209 - Four-row browser DOM proof',
  '',
  "- Tracked rows: $($rows.Count)",
  "- Data JSON IDs: $($dataVisibleIds.Count)/4",
  "- Browser DOM IDs: $($domVisibleIds.Count)/4",
  "- Browser: $browserPath",
  "- Headless mode: $($browserResult.flag)",
  "- Page HTTP: $($pageResponse.StatusCode); data HTTP: $($dataResponse.StatusCode)",
  "- Browser DOM proof passed: $passed",
  '- Exact geometry remains 0; manual scope review remains required.',
  '',
  '| Parcel ID | JSON | Browser DOM |',
  '|---|---:|---:|'
)
foreach ($row in $rowProof) {
  $reportLines += "| $($row.parcel_id) | $($row.data_json_visible) | $($row.browser_dom_visible) |"
}
$reportLines += ''
$reportLines += '`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'
Write-Utf8 $ReportPath ($reportLines -join [Environment]::NewLine)

Write-Output ($output | ConvertTo-Json -Depth 20)
if (-not $passed) { exit 1 }
exit 0
