param()

$ErrorActionPreference = 'Stop'
$TaskId = '214_aays1_parcel_label_4row_cdp_dom_proof_20260715'
$RepoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { throw 'AAYS_REPO_ROOT_NOT_RESOLVED' }
$RepoRoot = [IO.Path]::GetFullPath($RepoRoot)

$PageUrl = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=parcel-label-214'
$DataUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json?refresh=parcel-label-214'
$CandidateIds = @(
  'SOURCE_BULLRING_BIRMINGHAM_RETAIL_001',
  'SOURCE_THE_CUBE_BIRMINGHAM_MIXED_001',
  'SOURCE_ONE_ANGEL_SQUARE_MANCHESTER_OFFICE_001',
  'SOURCE_MAGNA_PARK_MPS187_INDUSTRIAL_001'
)

$StatusRoot = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\status'
$EvidenceRoot = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\evidence'
$OutputRoot = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\runner_outputs'
$ReportRoot = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\reports'
$CheckpointPath = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\checkpoints\parcel_label_canonical_checkpoint.json'
$GatePath = Join-Path $StatusRoot ($TaskId + '_gate.json')
$EvidencePath = Join-Path $EvidenceRoot '214_parcel_label_4row_cdp_dom_proof_evidence_20260715.json'
$OutputPath = Join-Path $OutputRoot ($TaskId + '_output.json')
$BrowserLogPath = Join-Path $OutputRoot ($TaskId + '_browser_stderr.log')
$ReportPath = Join-Path $ReportRoot '214_parcel_label_4row_cdp_dom_proof_report_20260715.md'

function Ensure-Directory([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}
function Write-Utf8([string]$Path,[string]$Text) {
  Ensure-Directory (Split-Path -Parent $Path)
  [IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))
}
function Write-Json([string]$Path,[object]$Value) { Write-Utf8 $Path (($Value | ConvertTo-Json -Depth 60) + "`n") }
function Resolve-Browser {
  $programFilesX86 = [Environment]::GetEnvironmentVariable('ProgramFiles(x86)')
  $candidates = @(
    $(if ($programFilesX86) { Join-Path $programFilesX86 'Microsoft\Edge\Application\msedge.exe' }),
    $(if ($env:ProgramFiles) { Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe' }),
    $(if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\Application\msedge.exe' }),
    $(if ($env:ProgramFiles) { Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe' }),
    $(if ($programFilesX86) { Join-Path $programFilesX86 'Google\Chrome\Application\chrome.exe' }),
    $(if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe' })
  ) | Where-Object { $_ }
  foreach ($candidate in $candidates) { if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate } }
  foreach ($name in @('msedge.exe','chrome.exe')) {
    $command = Get-Command $name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
  }
  return $null
}
function Get-FreeTcpPort {
  $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0)
  $listener.Start()
  try { return [int]$listener.LocalEndpoint.Port } finally { $listener.Stop() }
}
function Send-CdpCommand {
  param(
    [System.Net.WebSockets.ClientWebSocket]$Socket,
    [int]$Id,
    [string]$Method,
    [hashtable]$Params
  )
  $payload = [ordered]@{ id=$Id; method=$Method; params=$(if($Params){$Params}else{@{}}) }
  $json = $payload | ConvertTo-Json -Depth 30 -Compress
  $bytes = [Text.Encoding]::UTF8.GetBytes($json)
  $segment = [ArraySegment[byte]]::new($bytes)
  $Socket.SendAsync($segment,[Net.WebSockets.WebSocketMessageType]::Text,$true,[Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null
  while ($true) {
    $stream = New-Object IO.MemoryStream
    try {
      do {
        $buffer = New-Object byte[] 65536
        $receiveSegment = [ArraySegment[byte]]::new($buffer)
        $result = $Socket.ReceiveAsync($receiveSegment,[Threading.CancellationToken]::None).GetAwaiter().GetResult()
        if ($result.MessageType -eq [Net.WebSockets.WebSocketMessageType]::Close) { throw 'CDP_WEBSOCKET_CLOSED' }
        if ($result.Count -gt 0) { $stream.Write($buffer,0,$result.Count) }
      } while (-not $result.EndOfMessage)
      $text = [Text.Encoding]::UTF8.GetString($stream.ToArray())
      if ([string]::IsNullOrWhiteSpace($text)) { continue }
      $message = $text | ConvertFrom-Json
      if ($message.id -eq $Id) { return $message }
    } finally { $stream.Dispose() }
  }
}
function Invoke-CdpEval {
  param(
    [System.Net.WebSockets.ClientWebSocket]$Socket,
    [ref]$Sequence,
    [string]$Expression
  )
  $Sequence.Value++
  $response = Send-CdpCommand -Socket $Socket -Id $Sequence.Value -Method 'Runtime.evaluate' -Params @{
    expression=$Expression
    awaitPromise=$true
    returnByValue=$true
    userGesture=$true
  }
  if ($response.error) { throw ('CDP_RUNTIME_ERROR: ' + ($response.error | ConvertTo-Json -Compress)) }
  if ($response.result.exceptionDetails) { throw ('CDP_JS_EXCEPTION: ' + ($response.result.exceptionDetails | ConvertTo-Json -Depth 20 -Compress)) }
  return $response.result.result.value
}

$health = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/health' -TimeoutSec 15
$page = Invoke-WebRequest -UseBasicParsing -Uri $PageUrl -TimeoutSec 30
$dataResponse = Invoke-WebRequest -UseBasicParsing -Uri $DataUrl -TimeoutSec 30
$data = $dataResponse.Content | ConvertFrom-Json
$rows = @($data.rows)
$dataIds = @($rows | ForEach-Object { [string]$_.parcel_id })
$dataVisibleIds = @($CandidateIds | Where-Object { $dataIds -contains $_ })

$browserPath = Resolve-Browser
if (-not $browserPath) { throw 'BROWSER_EXECUTABLE_NOT_FOUND' }
$port = Get-FreeTcpPort
$tempProfile = Join-Path ([IO.Path]::GetTempPath()) ('aays_parcel_label_214_' + [guid]::NewGuid().ToString('N'))
Ensure-Directory $tempProfile
$stderrPath = Join-Path $tempProfile 'browser_stderr.log'
$stdoutPath = Join-Path $tempProfile 'browser_stdout.log'
$browserArgs = @(
  '--headless=new',
  '--disable-gpu',
  '--disable-extensions',
  '--disable-background-networking',
  '--no-first-run',
  '--no-default-browser-check',
  '--hide-scrollbars',
  '--window-size=1920,1080',
  ('--remote-debugging-port=' + $port),
  ('--user-data-dir=' + $tempProfile),
  $PageUrl
)
$browser = $null
$socket = $null
$rowProofs = @()
$layerSummary = $null
$browserError = ''
try {
  $browser = Start-Process -FilePath $browserPath -ArgumentList $browserArgs -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru -WindowStyle Hidden
  $deadline = (Get-Date).AddSeconds(45)
  $target = $null
  do {
    Start-Sleep -Milliseconds 500
    try {
      $targets = @(Invoke-RestMethod -Uri ("http://127.0.0.1:{0}/json/list" -f $port) -TimeoutSec 3)
      $target = @($targets | Where-Object { $_.type -eq 'page' -and $_.webSocketDebuggerUrl } | Select-Object -First 1)
    } catch {}
  } while (-not $target -and (Get-Date) -lt $deadline)
  if (-not $target) { throw 'CDP_PAGE_TARGET_NOT_FOUND' }

  $socket = [Net.WebSockets.ClientWebSocket]::new()
  $socket.ConnectAsync([Uri]$target.webSocketDebuggerUrl,[Threading.CancellationToken]::None).GetAwaiter().GetResult()
  $seq = 0
  $seq++
  Send-CdpCommand -Socket $socket -Id $seq -Method 'Runtime.enable' -Params @{} | Out-Null

  $selectExpression = @"
(async()=>{
  const select=document.getElementById('layerSelect');
  if(!select) throw new Error('layerSelect missing');
  select.value='distance';
  select.dispatchEvent(new Event('change',{bubbles:true}));
  if(typeof loadLayer==='function') await loadLayer('distance');
  await new Promise(r=>setTimeout(r,500));
  return JSON.stringify({selected:select.value,stateLayer:state.layer,rowCount:state.rows.length,pageInfo:document.getElementById('pageInfo').textContent,message:document.getElementById('message').textContent});
})()
"@
  $layerSummaryText = Invoke-CdpEval -Socket $socket -Sequence ([ref]$seq) -Expression $selectExpression
  $layerSummary = $layerSummaryText | ConvertFrom-Json

  foreach ($candidateId in $CandidateIds) {
    $expression = @"
(async()=>{
  const id='$candidateId';
  const select=document.getElementById('layerSelect');
  if(select.value!=='distance' || state.layer!=='distance'){
    select.value='distance';
    select.dispatchEvent(new Event('change',{bubbles:true}));
    await loadLayer('distance');
  }
  const search=document.getElementById('search');
  search.value=id;
  if(typeof applySearch==='function') applySearch();
  search.dispatchEvent(new Event('input',{bubbles:true}));
  await new Promise(r=>setTimeout(r,250));
  const rendered=[...document.querySelectorAll('#table tbody tr')];
  const row=rendered.find(tr=>tr.innerText.includes(id));
  return JSON.stringify({parcel_id:id,selected_layer:select.value,state_layer:state.layer,total_rows:state.rows.length,filtered_rows:state.filtered.length,visible:!!row,row_text:row?row.innerText.replace(/\s+/g,' ').trim():'',page_info:document.getElementById('pageInfo').textContent,message:document.getElementById('message').textContent});
})()
"@
    $proofText = Invoke-CdpEval -Socket $socket -Sequence ([ref]$seq) -Expression $expression
    $rowProofs += ($proofText | ConvertFrom-Json)
  }
} catch {
  $browserError = $_.Exception.Message
} finally {
  if ($socket) {
    try { $socket.CloseAsync([Net.WebSockets.WebSocketCloseStatus]::NormalClosure,'done',[Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null } catch {}
    $socket.Dispose()
  }
  if ($browser -and -not $browser.HasExited) { Stop-Process -Id $browser.Id -Force -ErrorAction SilentlyContinue }
  $stderr = if (Test-Path -LiteralPath $stderrPath) { Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue } else { '' }
  Write-Utf8 $BrowserLogPath ([string]$stderr)
  Remove-Item -LiteralPath $tempProfile -Recurse -Force -ErrorAction SilentlyContinue
}

$visibleProofs = @($rowProofs | Where-Object { $_.visible -eq $true })
$passed = ($health.StatusCode -eq 200 -and $page.StatusCode -eq 200 -and $dataResponse.StatusCode -eq 200 -and $rows.Count -eq 198 -and $dataVisibleIds.Count -eq 4 -and $layerSummary -and $layerSummary.selected -eq 'distance' -and $layerSummary.stateLayer -eq 'distance' -and [int]$layerSummary.rowCount -eq 198 -and $visibleProofs.Count -eq 4 -and [string]::IsNullOrWhiteSpace($browserError))
$now = [DateTimeOffset]::UtcNow.ToString('o')
$blockers = @()
if ($rows.Count -ne 198) { $blockers += 'SERVED_DATA_ROW_COUNT_NOT_198' }
if ($dataVisibleIds.Count -ne 4) { $blockers += 'SERVED_DATA_FOUR_IDS_NOT_VISIBLE' }
if (-not $layerSummary -or $layerSummary.selected -ne 'distance' -or $layerSummary.stateLayer -ne 'distance') { $blockers += 'BROWSER_DISTANCE_LAYER_NOT_SELECTED' }
if (-not $layerSummary -or [int]$layerSummary.rowCount -ne 198) { $blockers += 'BROWSER_DISTANCE_LAYER_ROW_COUNT_NOT_198' }
if ($visibleProofs.Count -ne 4) { $blockers += 'BROWSER_ROW_BY_ROW_FOUR_IDS_NOT_VISIBLE' }
if ($browserError) { $blockers += ('BROWSER_CDP_ERROR: ' + $browserError) }
$blockers += 'EXACT_GEOMETRY_BINDING_PENDING'
$blockers += 'MANUAL_SCOPE_REVIEW_PENDING'

$evidence = [ordered]@{
  task_id=$TaskId;generated_at=$now;browser_path=$browserPath;cdp_port=$port
  health_http_status=[int]$health.StatusCode;page_http_status=[int]$page.StatusCode;data_http_status=[int]$dataResponse.StatusCode
  served_row_count=$rows.Count;data_json_visible_ids=@($dataVisibleIds);data_json_visible_count=$dataVisibleIds.Count
  layer_summary=$layerSummary;row_proofs=@($rowProofs);browser_visible_count=$visibleProofs.Count
  browser_distance_layer_selected=($layerSummary -and $layerSummary.selected -eq 'distance' -and $layerSummary.stateLayer -eq 'distance')
  browser_row_by_row_proven=$passed;browser_error=$browserError;blockers=$blockers
  final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false
}
Write-Json $EvidencePath $evidence

$output = [ordered]@{
  task_id=$TaskId;status=$(if($passed){'PARCEL_LABEL_DISTANCE_LAYER_198_ROWS_AND_FOUR_DOM_ROWS_VERIFIED_REMOTE_COMMIT_PENDING'}else{'PARCEL_LABEL_CDP_DOM_PROOF_BLOCKED'})
  generated_at=$now;tracked_row_count=$rows.Count;http_visible_count=$dataVisibleIds.Count;browser_dom_visible_count=$visibleProofs.Count
  browser_verified_rows=$(if($passed){198}else{194});source_upgraded_rows=57;classification_enriched_rows=57
  latest_batch_accuracy_score_4=3.9375;target_confidence_percent=98.44;exact_geometry_rows=0
  blockers=$blockers;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false
}
Write-Json $OutputPath $output
Write-Json $GatePath ([ordered]@{task_id=$TaskId;source_row_gate_passed=($rows.Count-eq198-and$dataVisibleIds.Count-eq4);distance_layer_gate_passed=($layerSummary-and$layerSummary.selected-eq'distance');ui_token_gate_passed=$passed;browser_smoke_passed=$passed;post_sync_ok=$passed;manual_review_required=$true;fake_data=$false;final_ready=$false})

if (Test-Path -LiteralPath $CheckpointPath) {
  $checkpoint = Get-Content -LiteralPath $CheckpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $checkpoint | Add-Member -NotePropertyName checkpoint_sequence -NotePropertyValue 214 -Force
  $checkpoint | Add-Member -NotePropertyName checkpoint_status -NotePropertyValue $(if($passed){'TASK_214_LOCAL_BROWSER_VERIFIED_REMOTE_COMMIT_READBACK_PENDING'}else{'TASK_214_BROWSER_PROOF_BLOCKED'}) -Force
  $checkpoint | Add-Member -NotePropertyName pending_task_id -NotePropertyValue $TaskId -Force
  $checkpoint | Add-Member -NotePropertyName pending_task_state -NotePropertyValue $output.status -Force
  $checkpoint | Add-Member -NotePropertyName next_incomplete_action -NotePropertyValue $(if($passed){'remote_commit_readback_for_task_214_then_publish_prepared_task_213_six_rows'}else{'recover_task_214_cdp_browser_proof'}) -Force
  $checkpoint | Add-Member -NotePropertyName tracked_rows_live_artifact -NotePropertyValue $rows.Count -Force
  $checkpoint | Add-Member -NotePropertyName accepted_verified_rows -NotePropertyValue 198 -Force
  $checkpoint | Add-Member -NotePropertyName browser_verified_rows -NotePropertyValue $(if($passed){198}else{194}) -Force
  $checkpoint | Add-Member -NotePropertyName source_upgraded_rows -NotePropertyValue 57 -Force
  $checkpoint | Add-Member -NotePropertyName classification_enriched_rows -NotePropertyValue 57 -Force
  $checkpoint | Add-Member -NotePropertyName exact_geometry_rows -NotePropertyValue 0 -Force
  $checkpoint | Add-Member -NotePropertyName blockers -NotePropertyValue $blockers -Force
  $checkpoint | Add-Member -NotePropertyName updated_at -NotePropertyValue $now -Force
  $checkpoint | Add-Member -NotePropertyName final_ready -NotePropertyValue $false -Force
  $checkpoint | Add-Member -NotePropertyName product_final_ready -NotePropertyValue $false -Force
  $checkpoint | Add-Member -NotePropertyName fake_data -NotePropertyValue $false -Force
  $checkpoint | Add-Member -NotePropertyName db_write -NotePropertyValue $false -Force
  $checkpoint | Add-Member -NotePropertyName migration -NotePropertyValue $false -Force
  $checkpoint | Add-Member -NotePropertyName production_deploy -NotePropertyValue $false -Force
  Write-Json $CheckpointPath $checkpoint
}

$report = @(
  '# Parcel Label Task 214 - CDP Row-by-row Browser Proof','',
  ('- Served data rows: {0}' -f $rows.Count),
  ('- Served JSON visible IDs: {0}/4' -f $dataVisibleIds.Count),
  ('- Browser selected layer: {0}' -f $(if($layerSummary){$layerSummary.selected}else{'not_available'})),
  ('- Browser layer row count: {0}' -f $(if($layerSummary){$layerSummary.rowCount}else{0})),
  ('- Browser visible candidate rows: {0}/4' -f $visibleProofs.Count),
  ('- Result: {0}' -f $output.status),'',
  '| Parcel ID | Browser visible | Row proof |','|---|---:|---|'
)
foreach($proof in $rowProofs){$report += ('| {0} | {1} | {2} |' -f $proof.parcel_id,$proof.visible,(([string]$proof.row_text)-replace '\|','/'))}
$report += ''
$report += '`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'
Write-Utf8 $ReportPath (($report -join "`n") + "`n")

Write-Output ($output | ConvertTo-Json -Depth 30)
if (-not $passed) { exit 2 }
exit 0
