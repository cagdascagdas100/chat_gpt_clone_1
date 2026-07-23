$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$slotId = if ($env:AAYS_SLOT_ID) { [string]$env:AAYS_SLOT_ID } else { 'security_public_safety_3' }
$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'security-public-safety-3-resume-9147406c4a5f' }
$continuationKey = '9147406c4a5fb6fbd06910dddf2b38c200878a801d5bb0907aaf395f6170d1da'
if ($slotId -ne 'security_public_safety_3') { Write-Error "SLOT_ID_MISMATCH:$slotId"; exit 2 }

$repoRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
if (-not $repoRoot) { Write-Error 'REPO_ROOT_UNAVAILABLE'; exit 2 }

$baseUrl = if ($env:AAYS_BASE_URL) { ([string]$env:AAYS_BASE_URL).TrimEnd('/') } else { 'http://127.0.0.1:8012' }
$slotRootRelative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3'
$webRootRelative = 'england_map_web/data/aays_21_slots/security_public_safety_3'
$runStamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMdd_HHmmss')
$outputRootRelative = "$slotRootRelative/runner_outputs/runtime_browser_acceptance_$runStamp"
$outputRoot = Join-Path $repoRoot $outputRootRelative
$statusRelative = "$slotRootRelative/status/runtime_browser_acceptance_latest.json"
$operationRelative = "$webRootRelative/runtime_browser_acceptance_latest.json"
$statusPath = Join-Path $repoRoot $statusRelative
$operationPath = Join-Path $repoRoot $operationRelative
New-Item -ItemType Directory -Force -Path $outputRoot,(Split-Path $statusPath),(Split-Path $operationPath) | Out-Null

function Write-Utf8NoBom([string]$Path,[string]$Text){$parent=Split-Path $Path;if($parent){New-Item -ItemType Directory -Force -Path $parent|Out-Null};[IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))}
function Write-JsonNoBom([string]$Path,$Value){Write-Utf8NoBom $Path (($Value|ConvertTo-Json -Depth 80)+"`n")}
function Get-Sha256([string]$Path){if(-not(Test-Path -LiteralPath $Path)){return $null};return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Add-Unique([Collections.Generic.List[string]]$List,[string]$Value){if($Value -and -not $List.Contains($Value)){$List.Add($Value)}}

$startedAt=[DateTimeOffset]::UtcNow.ToString('o')
$blockers=[Collections.Generic.List[string]]::new()
$httpSpecs=@(
  [ordered]@{name='health';url="$baseUrl/health";required_status=200;path=(Join-Path $outputRoot 'health.txt')},
  [ordered]@{name='matrix_html';url="$baseUrl/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html";required_status=200;path=(Join-Path $outputRoot 'matrix.html')},
  [ordered]@{name='security_rows_json';url="$baseUrl/england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json";required_status=200;path=(Join-Path $outputRoot 'security_public_safety_visible_rows.json')}
)
$httpResults=[Collections.Generic.List[object]]::new()
foreach($spec in $httpSpecs){
  $status=0;$attempts=0;$errorText=$null
  for($attempt=1;$attempt -le 18;$attempt++){
    $attempts=$attempt
    try{
      $response=Invoke-WebRequest -UseBasicParsing -Uri $spec.url -TimeoutSec 20
      $status=[int]$response.StatusCode
      Write-Utf8NoBom $spec.path ([string]$response.Content)
      if($status -eq 200){break}
    }catch{$status=0;$errorText=$_.Exception.Message}
    if($attempt -lt 18){Start-Sleep -Seconds 10}
  }
  $hash=Get-Sha256 $spec.path
  $result=[ordered]@{name=$spec.name;url=$spec.url;status=$status;attempts=$attempts;sha256=$hash;artifact_path=$spec.path.Substring($repoRoot.Length).TrimStart('\','/').Replace('\','/');error=$errorText}
  $httpResults.Add($result)
  if($status -ne [int]$spec.required_status){Add-Unique $blockers ("HTTP_STATUS_NOT_200_{0}:{1}" -f $spec.name,$status)}
  if(-not $hash){Add-Unique $blockers ("HTTP_HASH_MISSING_{0}" -f $spec.name)}
}

$rowsJsonPath=($httpSpecs|Where-Object name -eq 'security_rows_json').path
$servedRowCount=0
if(Test-Path -LiteralPath $rowsJsonPath){try{$served=Get-Content -LiteralPath $rowsJsonPath -Raw -Encoding UTF8|ConvertFrom-Json;$servedRowCount=@($served.rows).Count}catch{Add-Unique $blockers ('SECURITY_JSON_PARSE_FAILED:'+ $_.Exception.Message)}}
if($servedRowCount -ne 300){Add-Unique $blockers ("SERVED_SECURITY_ROW_COUNT_MISMATCH:$servedRowCount/300")}

$portableRoot=if($env:AAYS_PORTABLE_ROOT){[string]$env:AAYS_PORTABLE_ROOT}else{$null}
if(-not $portableRoot){$cursor=$repoRoot;while($cursor -and (Split-Path -Leaf $cursor) -ne 'runner_system'){$parent=Split-Path -Parent $cursor;if(-not $parent -or $parent -eq $cursor){break};$cursor=$parent};if($cursor -and (Split-Path -Leaf $cursor) -eq 'runner_system'){$portableRoot=Split-Path -Parent $cursor}}
$browserPaths=[Collections.Generic.List[string]]::new()
if($portableRoot){foreach($rel in @('runtime/browser/chrome.exe','runtime/chrome/chrome.exe','runtime/chromium/chrome.exe','runtime/msedge/msedge.exe')){$browserPaths.Add((Join-Path $portableRoot $rel))}}
if(${env:ProgramFiles(x86)}){$browserPaths.Add((Join-Path ${env:ProgramFiles(x86)} 'Microsoft/Edge/Application/msedge.exe'));$browserPaths.Add((Join-Path ${env:ProgramFiles(x86)} 'Google/Chrome/Application/chrome.exe'))}
if($env:ProgramFiles){$browserPaths.Add((Join-Path $env:ProgramFiles 'Microsoft/Edge/Application/msedge.exe'));$browserPaths.Add((Join-Path $env:ProgramFiles 'Google/Chrome/Application/chrome.exe'))}
$browser=@($browserPaths|Where-Object{$_ -and(Test-Path -LiteralPath $_)}|Select-Object -Unique)|Select-Object -First 1
if(-not $browser){Add-Unique $blockers 'HEADLESS_BROWSER_NOT_FOUND'}

$browserProcess=$null;$socket=$null;$consoleErrors=[Collections.Generic.List[string]]::new();$runtimeExceptions=[Collections.Generic.List[string]]::new();$logErrors=[Collections.Generic.List[string]]::new();$domEvidence=$null;$browserExitCode=$null
function Receive-Cdp([System.Net.WebSockets.ClientWebSocket]$Socket,[int]$TimeoutMs){
  $buffer=New-Object byte[] 65536;$segment=[ArraySegment[byte]]::new($buffer);$stream=[IO.MemoryStream]::new();$cts=[Threading.CancellationTokenSource]::new($TimeoutMs)
  try{do{$r=$Socket.ReceiveAsync($segment,$cts.Token).GetAwaiter().GetResult();if($r.MessageType-eq[Net.WebSockets.WebSocketMessageType]::Close){return $null};$stream.Write($buffer,0,$r.Count)}while(-not$r.EndOfMessage);return [Text.Encoding]::UTF8.GetString($stream.ToArray())}catch{return $null}finally{$stream.Dispose();$cts.Dispose()}
}
$script:cdpId=0
function Send-Cdp([System.Net.WebSockets.ClientWebSocket]$Socket,[string]$Method,$Params){$script:cdpId++;$payload=[ordered]@{id=$script:cdpId;method=$Method;params=$Params}|ConvertTo-Json -Depth 30 -Compress;$bytes=[Text.Encoding]::UTF8.GetBytes($payload);$Socket.SendAsync([ArraySegment[byte]]::new($bytes),[Net.WebSockets.WebSocketMessageType]::Text,$true,[Threading.CancellationToken]::None).GetAwaiter().GetResult()|Out-Null;return $script:cdpId}
function Handle-CdpEvent($Message){
  if(-not $Message.method){return}
  if($Message.method-eq'Runtime.consoleAPICalled' -and @('error','assert') -contains [string]$Message.params.type){$text=(@($Message.params.args)|ForEach-Object{if($_.value){[string]$_.value}else{[string]$_.description}})-join' ';Add-Unique $consoleErrors $text}
  elseif($Message.method-eq'Runtime.exceptionThrown'){Add-Unique $runtimeExceptions ([string]$Message.params.exceptionDetails.text)}
  elseif($Message.method-eq'Log.entryAdded' -and [string]$Message.params.entry.level -eq 'error'){Add-Unique $logErrors ([string]$Message.params.entry.text)}
}
function Wait-CdpResponse([System.Net.WebSockets.ClientWebSocket]$Socket,[int]$Id,[int]$TimeoutMs){$deadline=[DateTime]::UtcNow.AddMilliseconds($TimeoutMs);while([DateTime]::UtcNow-lt$deadline){$raw=Receive-Cdp $Socket 1000;if(-not$raw){continue};try{$msg=$raw|ConvertFrom-Json}catch{continue};Handle-CdpEvent $msg;if($msg.id-eq$Id){return $msg}};return $null}
function Drain-Cdp([System.Net.WebSockets.ClientWebSocket]$Socket,[int]$Seconds){$deadline=[DateTime]::UtcNow.AddSeconds($Seconds);while([DateTime]::UtcNow-lt$deadline){$raw=Receive-Cdp $Socket 500;if(-not$raw){continue};try{$msg=$raw|ConvertFrom-Json}catch{continue};Handle-CdpEvent $msg}}

if($browser -and ($httpResults|Where-Object name -eq 'matrix_html').status -eq 200){
  try{
    $port=if($env:AAYS_CDP_PORT){[int]$env:AAYS_CDP_PORT}else{9237};$profile=Join-Path $outputRoot 'browser_profile';New-Item -ItemType Directory -Force -Path $profile|Out-Null
    $pageUrl="$baseUrl/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html"
    $args=@('--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--no-default-browser-check',"--remote-debugging-port=$port",("--user-data-dir="+$profile),$pageUrl)
    $browserProcess=Start-Process -FilePath $browser -ArgumentList $args -PassThru
    $target=$null
    for($i=0;$i-lt40;$i++){try{$targets=Invoke-RestMethod -Uri "http://127.0.0.1:$port/json/list" -TimeoutSec 2;$target=@($targets|Where-Object type -eq 'page'|Select-Object -First 1);if($target){break}}catch{};Start-Sleep -Milliseconds 500}
    if(-not$target){Add-Unique $blockers 'CDP_PAGE_TARGET_UNAVAILABLE'}else{
      $socket=[Net.WebSockets.ClientWebSocket]::new();$socket.ConnectAsync([Uri]$target.webSocketDebuggerUrl,[Threading.CancellationToken]::None).GetAwaiter().GetResult()
      foreach($method in @('Runtime.enable','Log.enable','Page.enable')){$id=Send-Cdp $socket $method @{};if(-not(Wait-CdpResponse $socket $id 5000)){Add-Unique $blockers ("CDP_ENABLE_TIMEOUT:$method")}}
      $navId=Send-Cdp $socket 'Page.navigate' @{url=$pageUrl};[void](Wait-CdpResponse $socket $navId 10000);Drain-Cdp $socket 8
      $expression=@"
(async()=>{
 const select=document.getElementById('layerSelect');
 if(!select) throw new Error('layerSelect missing');
 select.value='security';select.dispatchEvent(new Event('change',{bubbles:true}));
 const deadline=Date.now()+30000;
 while(Date.now()<deadline){if(typeof state!=='undefined'&&state.layer==='security'&&Array.isArray(state.rows)&&state.rows.length===300)break;await new Promise(r=>setTimeout(r,250));}
 return {selectedLayer:(typeof state!=='undefined'?state.layer:null),totalRows:(typeof state!=='undefined'&&Array.isArray(state.rows)?state.rows.length:0),filteredRows:(typeof state!=='undefined'&&Array.isArray(state.filtered)?state.filtered.length:0),renderedTableRows:document.querySelectorAll('#table tbody tr').length,message:(document.getElementById('message')||{}).textContent||'',title:(document.getElementById('title')||{}).textContent||''};
})()
"@
      $evalId=Send-Cdp $socket 'Runtime.evaluate' @{expression=$expression;awaitPromise=$true;returnByValue=$true};$eval=Wait-CdpResponse $socket $evalId 45000;Drain-Cdp $socket 3
      if(-not$eval){Add-Unique $blockers 'CDP_RUNTIME_EVALUATE_TIMEOUT'}elseif($eval.result.exceptionDetails){Add-Unique $blockers 'CDP_RUNTIME_EVALUATE_EXCEPTION'}else{$domEvidence=$eval.result.result.value}
    }
  }catch{Add-Unique $blockers ('BROWSER_CDP_EXCEPTION:'+ $_.Exception.Message)}
  finally{if($socket){try{$socket.Dispose()}catch{}};if($browserProcess){try{if(-not$browserProcess.HasExited){Stop-Process -Id $browserProcess.Id -Force};$browserExitCode=$browserProcess.ExitCode}catch{}}}
}

foreach($x in @($consoleErrors)){Add-Unique $blockers ('BROWSER_CONSOLE_ERROR:'+ $x)}
foreach($x in @($runtimeExceptions)){Add-Unique $blockers ('BROWSER_RUNTIME_EXCEPTION:'+ $x)}
foreach($x in @($logErrors)){Add-Unique $blockers ('BROWSER_LOG_ERROR:'+ $x)}
$selectedLayer=if($domEvidence){[string]$domEvidence.selectedLayer}else{$null}
$domRowCount=if($domEvidence){[int]$domEvidence.totalRows}else{0}
if($selectedLayer-ne'security'){Add-Unique $blockers ("BROWSER_SELECTED_LAYER_MISMATCH:$selectedLayer")}
if($domRowCount-ne300){Add-Unique $blockers ("BROWSER_DOM_SECURITY_ROW_COUNT_MISMATCH:$domRowCount/300")}
$pass=($blockers.Count-eq0 -and $servedRowCount-eq300 -and $selectedLayer-eq'security' -and $domRowCount-eq300 -and $consoleErrors.Count-eq0 -and $runtimeExceptions.Count-eq0 -and $logErrors.Count-eq0)
$statusName=if($pass){'RUNTIME_BROWSER_ACCEPTANCE_VERIFIED'}else{'RUNTIME_BROWSER_ACCEPTANCE_BLOCKED'}
$status=[ordered]@{schema_version=3;architecture_version=3;workstream_id='AAYS_21_SLOT_SAFE_PARALLEL_V1';slot_id=$slotId;task_id=$taskId;continuation_key=$continuationKey;status=$statusName;acceptance_pass=[bool]$pass;base_url=$baseUrl;http_results=$httpResults;served_security_row_count=$servedRowCount;browser_path=$browser;browser_exit_code=$browserExitCode;selected_layer=$selectedLayer;browser_dom_security_row_count=$domRowCount;browser_dom_evidence=$domEvidence;console_error_count=$consoleErrors.Count;runtime_exception_count=$runtimeExceptions.Count;browser_log_error_count=$logErrors.Count;console_errors=$consoleErrors;runtime_exceptions=$runtimeExceptions;browser_log_errors=$logErrors;blockers=@($blockers);output_root=$outputRootRelative;started_at=$startedAt;finished_at=[DateTimeOffset]::UtcNow.ToString('o');single_runner_only=$true;new_runner=$false;parallel_runner=$false;data_deleted=$false;force_push_used=$false;reset_hard_used=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false;final_ready=$false}
Write-JsonNoBom $statusPath $status
$operation=[ordered]@{schema_version=1;slot_id=$slotId;continuation_key=$continuationKey;generated_at=[DateTimeOffset]::UtcNow.ToString('o');operations=@([ordered]@{operation_id='security_public_safety_3_runtime_browser_acceptance';operation_type='runtime_browser_acceptance';stage='http_hash_cdp_dom_console';status=if($pass){'completed'}else{'blocked'};accuracy_score_4=4;confidence_score=if($pass){100}else{0};http_statuses=@($httpResults|ForEach-Object{"$($_.name)=$($_.status)"});http_sha256=@($httpResults|ForEach-Object{"$($_.name)=$($_.sha256)"});selected_layer=$selectedLayer;visible_rows=$domRowCount;console_error_count=$consoleErrors.Count;result=$statusName;evidence_path=$statusRelative;needs_manual_review=(-not$pass)})}
Write-JsonNoBom $operationPath $operation
if($pass){exit 0}else{exit 1}
