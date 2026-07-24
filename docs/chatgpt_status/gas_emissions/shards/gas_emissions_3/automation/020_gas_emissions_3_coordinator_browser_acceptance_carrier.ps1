[CmdletBinding()]
param(
    [int]$VirtualTimeBudgetMs = 180000,
    [int]$HttpTimeoutSeconds = 45
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$slotId = 'gas_emissions_3'
$branch = 'codex/aays-single-runner-v5-20260706'
$repoRoot = (Get-Location).Path.TrimEnd('\')
$acceptanceRoot = Join-Path $repoRoot 'docs\chatgpt_status\gas_emissions\shards\gas_emissions_3\acceptance'
$runtimeProofRoot = Join-Path $acceptanceRoot '020_coordinator_browser_runtime_latest'
$siteRoot = Join-Path $repoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3'
$resultPath = Join-Path $acceptanceRoot '012_gas_emissions_3_100_browser_acceptance_local_result_latest.json'
$statusPath = Join-Path $siteRoot 'browser_acceptance_runner_status_latest.json'
$pickupPath = Join-Path $siteRoot 'runner_pickup_preflight_latest.json'
$screenshotPath = Join-Path $acceptanceRoot '013_gas_emissions_3_matrix_browser_screenshot_latest.png'
$screenshotMetadataPath = Join-Path $acceptanceRoot '013_gas_emissions_3_matrix_browser_screenshot_latest.json'
$authoritativeCheckpointPath = Join-Path $repoRoot 'docs\chatgpt_status\_shared\slots_21\gas_emissions_3\checkpoint_latest.json'
$portableRoot = [string]$env:AAYS_PORTABLE_ROOT
$runtimeCheckpointPath = if ([string]::IsNullOrWhiteSpace($portableRoot)) { $null } else { Join-Path $portableRoot 'state\slots\gas_emissions_3\checkpoint_latest.json' }
$remoteTrackingRef = "refs/remotes/origin/$branch"
$wrapperRelative = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/automation/021_gas_emissions_3_queue_runtime_token_wrapper.ps1'
$carrierRelative = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/automation/020_gas_emissions_3_coordinator_browser_acceptance_carrier.ps1'
$harnessRelative = 'england_map_web/data/aays_18_slots/gas_emissions_3/canonical_matrix_100_browser_harness.html'

$precheckUrl = 'http://127.0.0.1:8012/england_map_web/data/aays_18_slots/gas_emissions_3/browser_acceptance_precheck.html?runner=coordinator-v11'
$matrixUrl = 'http://127.0.0.1:8012/england_map_web/data/aays_18_slots/gas_emissions_3/canonical_matrix_100_browser_harness.html?runner=coordinator-v11'
$canonicalMatrixUrl = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$visibleRowsUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
$matrixStatusUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
$summaryUrl = 'http://127.0.0.1:8012/england_map_web/data/aays_18_slots/gas_emissions_3/summary_latest.json'

New-Item -ItemType Directory -Force -Path $acceptanceRoot, $runtimeProofRoot, $siteRoot | Out-Null

$gitCandidates = @()
if (-not [string]::IsNullOrWhiteSpace($portableRoot)) {
    $gitCandidates += (Join-Path $portableRoot 'runtime\git\cmd\git.exe')
    $gitCandidates += (Join-Path $portableRoot 'runtime\git\bin\git.exe')
}
$gitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $gitCommand) { $gitCommand = Get-Command git -ErrorAction SilentlyContinue }
if ($gitCommand) { $gitCandidates += $gitCommand.Source }
$gitExe = $gitCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique | Select-Object -First 1
if (-not $gitExe) { throw 'Portable or system git executable was not found.' }
$gitExe = [string]$gitExe

function Write-Json($Value, [string]$Path) {
    $json = $Value | ConvertTo-Json -Depth 60
    $parent = Split-Path -Parent $Path
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [System.IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
}
function Invoke-Git([string[]]$GitArgs) {
    $output = & $gitExe -C $repoRoot @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) { throw "$gitExe $($GitArgs -join ' ') failed: $($output -join [Environment]::NewLine)" }
    return (($output -join [Environment]::NewLine).Trim())
}
function Sync-RemoteTrackingHead {
    $fetchArgs = @('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','fetch','--no-tags','--depth=64','origin',("+refs/heads/$branch`:$remoteTrackingRef"))
    [void](Invoke-Git $fetchArgs)
    return Invoke-Git @('rev-parse',$remoteTrackingRef)
}
function Assert-BlobParity([string]$Path,[string]$LocalRef,[string]$RemoteRef) {
    $localBlob = Invoke-Git @('rev-parse',"$LocalRef`:$Path")
    $remoteBlob = Invoke-Git @('rev-parse',"$RemoteRef`:$Path")
    if ($localBlob -ne $remoteBlob) { throw "Remote blob changed for $Path. local=$localBlob remote=$remoteBlob" }
    return $localBlob
}
function Assert-RemotePhase([string]$Phase,[string]$LocalHead,[string]$ValidatedRemoteHead) {
    $currentRemoteHead = Sync-RemoteTrackingHead
    $localMergeBase = Invoke-Git @('merge-base',$LocalHead,$currentRemoteHead)
    if ($localMergeBase -ne $LocalHead) { throw "$Phase local HEAD is not an ancestor of current remote. local=$LocalHead remote=$currentRemoteHead merge_base=$localMergeBase" }
    $validatedMergeBase = Invoke-Git @('merge-base',$ValidatedRemoteHead,$currentRemoteHead)
    if ($validatedMergeBase -ne $ValidatedRemoteHead) { throw "$Phase validated remote is not an ancestor of current remote. validated=$ValidatedRemoteHead current=$currentRemoteHead merge_base=$validatedMergeBase" }
    $wrapperBlob = Assert-BlobParity $wrapperRelative 'HEAD' $remoteTrackingRef
    $carrierBlob = Assert-BlobParity $carrierRelative 'HEAD' $remoteTrackingRef
    $harnessBlob = Assert-BlobParity $harnessRelative 'HEAD' $remoteTrackingRef
    return [ordered]@{phase=$Phase;current_remote_head=$currentRemoteHead;local_is_ancestor=$true;validated_remote_is_ancestor=$true;wrapper_blob_sha=$wrapperBlob;carrier_blob_sha=$carrierBlob;harness_blob_sha=$harnessBlob;blob_parity_count=3;passed=$true;checked_at=[DateTime]::UtcNow.ToString('o')}
}
function Invoke-HttpText([string]$Url) {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $HttpTimeoutSeconds -Headers @{'Cache-Control'='no-cache'}
    return [pscustomobject]@{url=$Url;status_code=[int]$response.StatusCode;content=[string]$response.Content;passed=([int]$response.StatusCode -eq 200)}
}
function Invoke-HttpJson([string]$Url) {
    $text = Invoke-HttpText $Url
    return [pscustomobject]@{url=$Url;status_code=$text.status_code;content=$text.content;json=($text.content | ConvertFrom-Json);passed=$text.passed}
}
function Find-Browser {
    $candidates = @()
    foreach ($name in @('msedge.exe','msedge','chrome.exe','chrome')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) { $candidates += $command.Source }
    }
    foreach ($root in @(${env:ProgramFiles(x86)},$env:ProgramFiles,$env:LOCALAPPDATA) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) {
        $candidates += (Join-Path $root 'Microsoft\Edge\Application\msedge.exe')
        $candidates += (Join-Path $root 'Google\Chrome\Application\chrome.exe')
    }
    $browser = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique | Select-Object -First 1
    if (-not $browser) { throw 'Installed Edge or Chrome executable was not found.' }
    return [string]$browser
}
function Invoke-DomDump([string]$Browser,[string]$Url,[string]$Label) {
    $profileDir = Join-Path $runtimeProofRoot ("profile_" + $Label)
    $stdoutPath = Join-Path $runtimeProofRoot ($Label + '_dom.html')
    $stderrPath = Join-Path $runtimeProofRoot ($Label + '_stderr.log')
    Remove-Item -Recurse -Force -LiteralPath $profileDir -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
    $arguments = @('--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update',"--user-data-dir=$profileDir","--virtual-time-budget=$VirtualTimeBudgetMs",'--dump-dom','--enable-logging=stderr','--log-level=3',$Url)
    & $Browser @arguments 1> $stdoutPath 2> $stderrPath
    $exitCode = $LASTEXITCODE
    $dom = if (Test-Path -LiteralPath $stdoutPath) { Get-Content -Raw -LiteralPath $stdoutPath } else { '' }
    $stderr = if (Test-Path -LiteralPath $stderrPath) { Get-Content -Raw -LiteralPath $stderrPath } else { '' }
    return [pscustomobject]@{label=$Label;url=$Url;exit_code=$exitCode;dom=$dom;stderr=$stderr;dom_path=$stdoutPath;stderr_path=$stderrPath;dom_sha256=if(Test-Path -LiteralPath $stdoutPath){(Get-FileHash -Algorithm SHA256 -LiteralPath $stdoutPath).Hash.ToLowerInvariant()}else{$null};stderr_sha256=if(Test-Path -LiteralPath $stderrPath){(Get-FileHash -Algorithm SHA256 -LiteralPath $stderrPath).Hash.ToLowerInvariant()}else{$null}}
}
function Read-PngDimensions([string]$Path) {
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 24) { throw 'PNG file is shorter than the required 24-byte header.' }
    $signature = [byte[]](137,80,78,71,13,10,26,10)
    for ($i=0; $i -lt $signature.Length; $i++) { if ($bytes[$i] -ne $signature[$i]) { throw 'Screenshot PNG signature is invalid.' } }
    $widthBytes = [byte[]]@($bytes[19],$bytes[18],$bytes[17],$bytes[16])
    $heightBytes = [byte[]]@($bytes[23],$bytes[22],$bytes[21],$bytes[20])
    return [ordered]@{signature_passed=$true;width=[int][BitConverter]::ToUInt32($widthBytes,0);height=[int][BitConverter]::ToUInt32($heightBytes,0)}
}
function Capture-Screenshot([string]$Browser,[string]$Url) {
    $profileDir = Join-Path $runtimeProofRoot 'profile_screenshot'
    $stderrPath = Join-Path $runtimeProofRoot 'screenshot_stderr.log'
    Remove-Item -Recurse -Force -LiteralPath $profileDir -ErrorAction SilentlyContinue
    Remove-Item -Force -LiteralPath $screenshotPath -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
    $arguments = @('--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update',"--user-data-dir=$profileDir",'--window-size=1920,1080',"--virtual-time-budget=$VirtualTimeBudgetMs",("--screenshot=" + $screenshotPath),$Url)
    & $Browser @arguments 1> $null 2> $stderrPath
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) { throw "Screenshot browser exited with code $exitCode" }
    if (-not (Test-Path -LiteralPath $screenshotPath -PathType Leaf)) { throw 'Screenshot file was not created.' }
    $info = Get-Item -LiteralPath $screenshotPath
    if ([int64]$info.Length -lt 10000) { throw "Screenshot file is unexpectedly small: $($info.Length) bytes" }
    $dimensions = Read-PngDimensions $screenshotPath
    if ($dimensions.width -ne 1920 -or $dimensions.height -ne 1080) { throw "Screenshot dimensions mismatch: $($dimensions.width)x$($dimensions.height)" }
    $stderr = if (Test-Path -LiteralPath $stderrPath) { Get-Content -Raw -LiteralPath $stderrPath } else { '' }
    $stderrError = $stderr -match '(?im)(uncaught|unhandled|javascript error|console[^`r`n]*error)'
    if ($stderrError) { throw 'Screenshot browser stderr contains a script error marker.' }
    return [ordered]@{status='PASS';url=$Url;canonical_matrix_url=$canonicalMatrixUrl;browser_path=$Browser;exit_code=$exitCode;path='docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/acceptance/013_gas_emissions_3_matrix_browser_screenshot_latest.png';byte_count=[int64]$info.Length;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $screenshotPath).Hash.ToLowerInvariant();png_signature_passed=$dimensions.signature_passed;width=$dimensions.width;height=$dimensions.height;stderr_error_markers=0;stderr_path='docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/acceptance/020_coordinator_browser_runtime_latest/screenshot_stderr.log';stderr_sha256=if(Test-Path -LiteralPath $stderrPath){(Get-FileHash -Algorithm SHA256 -LiteralPath $stderrPath).Hash.ToLowerInvariant()}else{$null};captured_at=[DateTime]::UtcNow.ToString('o');remote_readback_required=$true}
}
function Count-Matches([string]$Text,[string]$Pattern) {
    if ([string]::IsNullOrEmpty($Text)) { return 0 }
    return [regex]::Matches($Text,$Pattern,[System.Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
}
function Repo-Relative([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($repoRoot,[StringComparison]::OrdinalIgnoreCase)) { throw "Path outside repository: $full" }
    return $full.Substring($repoRoot.Length).TrimStart('\').Replace('\','/')
}

try {
    if ([string]$env:AAYS_SLOT_ID -ne $slotId) { throw "AAYS_SLOT_ID mismatch: $env:AAYS_SLOT_ID" }
    if ([string]$env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN -ne 'true') { throw 'Coordinator child direct-push guard is not active.' }
    $localHead = Invoke-Git @('rev-parse','HEAD')
    $validatedLocalHead = [string]$env:AAYS_VALIDATED_LOCAL_HEAD
    $validatedRemoteHead = [string]$env:AAYS_VALIDATED_REMOTE_HEAD
    $headRelation = [string]$env:AAYS_REMOTE_HEAD_RELATION
    $remoteBlobParity = [string]$env:AAYS_REMOTE_BLOB_PARITY
    if ($validatedLocalHead -ne $localHead) { throw "Wrapper/carrier local HEAD mismatch. wrapper=$validatedLocalHead carrier=$localHead" }
    if ([string]::IsNullOrWhiteSpace($validatedRemoteHead) -or $headRelation -ne 'LOCAL_ANCESTOR_OF_REMOTE' -or $remoteBlobParity -ne 'true') { throw 'Wrapper remote ancestry/blob parity evidence is missing.' }
    $remotePhaseBefore = Assert-RemotePhase 'BEFORE_BROWSER' $localHead $validatedRemoteHead

    if (-not (Test-Path -LiteralPath $authoritativeCheckpointPath -PathType Leaf)) { throw "Authoritative checkpoint missing: $authoritativeCheckpointPath" }
    $authoritativeCheckpoint = Get-Content -Raw -LiteralPath $authoritativeCheckpointPath | ConvertFrom-Json
    if ($authoritativeCheckpoint.slot_id -ne $slotId) { throw 'Authoritative checkpoint slot mismatch.' }
    if ([int]$authoritativeCheckpoint.sequence -lt 24) { throw "Authoritative checkpoint sequence regressed: $($authoritativeCheckpoint.sequence)" }
    if (-not $runtimeCheckpointPath) { throw 'AAYS_PORTABLE_ROOT is required to preserve the coordinator runtime checkpoint.' }
    $runtimeCheckpoint = $authoritativeCheckpoint | Select-Object *
    $runtimeCheckpoint | Add-Member -NotePropertyName hydration_state -NotePropertyValue 'AUTHORITATIVE_REMOTE_SEQUENCE_PRESERVED_FOR_COORDINATOR_PUBLISH' -Force
    $runtimeCheckpoint | Add-Member -NotePropertyName updated_at -NotePropertyValue ([DateTime]::UtcNow.ToString('o')) -Force
    $runtimeCheckpoint | Add-Member -NotePropertyName validated_remote_head -NotePropertyValue $validatedRemoteHead -Force
    $runtimeCheckpoint | Add-Member -NotePropertyName browser_phase_remote_head -NotePropertyValue $remotePhaseBefore.current_remote_head -Force
    Write-Json $runtimeCheckpoint $runtimeCheckpointPath

    $precheckHttp = Invoke-HttpText $precheckUrl
    $matrixHttp = Invoke-HttpText $matrixUrl
    $visibleRowsHttp = Invoke-HttpJson $visibleRowsUrl
    $matrixStatusHttp = Invoke-HttpJson $matrixStatusUrl
    $summaryHttp = Invoke-HttpJson $summaryUrl
    $visibleRows = @($visibleRowsHttp.json.rows)
    $servedRows = $visibleRows.Count
    $uniqueRows = @($visibleRows | ForEach-Object { $_.row_id } | Sort-Object -Unique).Count
    $matrixRows = [int]$matrixStatusHttp.json.visible_rows_count
    $candidateRows = [int]$summaryHttp.json.metrics.revision_candidates
    $httpPassed = @($precheckHttp,$matrixHttp,$visibleRowsHttp,$matrixStatusHttp,$summaryHttp).Where({$_.passed}).Count -eq 5
    $servedPassed = $servedRows -eq 100 -and $uniqueRows -eq 100 -and $matrixRows -eq 100 -and $candidateRows -eq 100

    $browser = Find-Browser
    $precheck = Invoke-DomDump $browser $precheckUrl 'precheck'
    $matrix = Invoke-DomDump $browser $matrixUrl 'matrix'
    $screenshot = Capture-Screenshot $browser $matrixUrl
    Write-Json $screenshot $screenshotMetadataPath

    $precheckPassRows = Count-Matches $precheck.dom '<tr[^>]*class=["'']pass["'']'
    $precheckFailRows = Count-Matches $precheck.dom '<tr[^>]*class=["'']fail["'']'
    $precheckPassed = $precheck.exit_code -eq 0 -and $precheckPassRows -eq 100 -and $precheckFailRows -eq 0 -and $precheck.dom -match 'PRECHECK_PASS_NOT_BROWSER_ACCEPTANCE'
    $requiredHeaders = @('Durum','Satır','Yıl','Sektör','Alt sektör','Sera gazı','Emisyon \(kt CO2e\)','Etki alanı \(kt CO2\)','Kaynak satırı','Eşleştirme yöntemi','Hesap açıklaması','Parcel binding','Güven \(%\)','Doğruluk','Resmi kaynak URL','Ham yerel kaynak','Visible artifact','Status yolu','Rapor yolu','Served commit','Artifact SHA','Manuel inceleme','Resmi CSV eşleşmesi','Kaynak SHA-256','Kaynak manifesti','Satır kanıtı','Pipeline','Blocker')
    $missingHeaders = @($requiredHeaders | Where-Object { $matrix.dom -notmatch $_ })
    $matrixAcceptanceRows = Count-Matches $matrix.dom 'data-acceptance-row=["'']true["'']'
    $matrixAcceptanceHeaders = Count-Matches $matrix.dom 'data-acceptance-header=["'']true["'']'
    $matrixPassMarker = $matrix.dom -match 'data-acceptance-complete=["'']true["'']' -and $matrix.dom -match 'data-acceptance-state=["'']PASS["'']'
    $matrixPageEvidence = $matrix.dom -match 'data-canonical-pages=["'']4["'']' -and $matrix.dom -match 'data-page-row-count=["'']25["'']' -and $matrix.dom -match 'data-unique-rows=["'']100["'']'
    $matrixPassed = $matrix.exit_code -eq 0 -and $matrixPassMarker -and $matrixPageEvidence -and $matrixAcceptanceRows -eq 100 -and $matrixAcceptanceHeaders -eq 28 -and $missingHeaders.Count -eq 0
    $scriptErrors = @()
    foreach ($entry in @($precheck,$matrix)) { if ($entry.stderr -match '(?im)(uncaught|unhandled|javascript error|console[^`r`n]*error)') { $scriptErrors += "$($entry.label): browser stderr contains a script error marker" } }
    $browserDomPassed = $httpPassed -and $servedPassed -and $precheckPassed -and $matrixPassed -and $scriptErrors.Count -eq 0
    if (-not $browserDomPassed) { throw "Browser acceptance failed. http=$httpPassed served=$servedPassed precheck=$precheckPassed matrix=$matrixPassed rows=$matrixAcceptanceRows headers=$matrixAcceptanceHeaders errors=$($scriptErrors.Count)" }

    $remotePhaseAfter = Assert-RemotePhase 'AFTER_BROWSER' $localHead $validatedRemoteHead
    $generatedAt = [DateTime]::UtcNow.ToString('o')
    $gitEvidence = [ordered]@{local_head=$localHead;validated_remote_head=$validatedRemoteHead;remote_phase_before=$remotePhaseBefore;remote_phase_after=$remotePhaseAfter;two_phase_remote_parity_passed=$true;direct_child_push_forbidden=$true;coordinator_serial_publish_required=$true;remote_publish_readback_passed=$false}
    $result = [ordered]@{schema_version=7;slot_id=$slotId;generated_at=$generatedAt;status='COORDINATOR_V11_TWO_PHASE_REMOTE_PARITY_EXACT_DOM_PNG_PASS_AWAITING_SERIAL_REMOTE_PUBLISH_READBACK';runner_policy='EXISTING_CANONICAL_F_SHARED_RUNNER_ONLY';runner_version=11;browser_path=$browser;git_executable=$gitExe;git=$gitEvidence;http=[ordered]@{endpoint_count=5;all_status_200=$httpPassed;served_row_count=$servedRows;served_unique_row_count=$uniqueRows;matrix_status_row_count=$matrixRows;summary_candidate_count=$candidateRows;passed=$servedPassed};precheck=[ordered]@{url=$precheckUrl;exit_code=$precheck.exit_code;pass_rows=$precheckPassRows;fail_rows=$precheckFailRows;dom_path=(Repo-Relative $precheck.dom_path);dom_sha256=$precheck.dom_sha256;stderr_path=(Repo-Relative $precheck.stderr_path);stderr_sha256=$precheck.stderr_sha256;passed=$precheckPassed};matrix=[ordered]@{harness_url=$matrixUrl;canonical_url=$canonicalMatrixUrl;exit_code=$matrix.exit_code;expected_pages=4;expected_rows_per_page=25;expected_rows=100;actual_dom_rows=$matrixAcceptanceRows;actual_dom_headers=$matrixAcceptanceHeaders;unique_rows=100;pass_marker_present=$matrixPassMarker;page_evidence_present=$matrixPageEvidence;required_header_count=$requiredHeaders.Count;missing_headers=$missingHeaders;dom_path=(Repo-Relative $matrix.dom_path);dom_sha256=$matrix.dom_sha256;stderr_path=(Repo-Relative $matrix.stderr_path);stderr_sha256=$matrix.stderr_sha256;passed=$matrixPassed};screenshot=$screenshot;browser_script_errors=$scriptErrors;browser_dom_passed=$true;browser_acceptance_passed=$false;coordinator_publish_required=$true;parcel_binding_gate_passed=$false;measured_parcel_values_produced=0;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
    Write-Json $result $resultPath

    $steps = @(
        [ordered]@{step=1;name='VALIDATE_WRAPPER_LOCAL_AND_REMOTE_EVIDENCE';state='PASS';evidence="local=$localHead validated_remote=$validatedRemoteHead"},
        [ordered]@{step=2;name='REMOTE_PARITY_PHASE_ONE_BEFORE_BROWSER';state='PASS';evidence=$remotePhaseBefore.current_remote_head},
        [ordered]@{step=3;name='VERIFY_WRAPPER_CARRIER_HARNESS_BLOBS_PHASE_ONE';state='PASS';evidence='3/3'},
        [ordered]@{step=4;name='USE_PORTABLE_GIT';state='PASS';evidence=$gitExe},
        [ordered]@{step=5;name='PRESERVE_AUTHORITATIVE_CHECKPOINT_SEQUENCE';state='PASS';evidence="sequence=$($authoritativeCheckpoint.sequence)"},
        [ordered]@{step=6;name='CHECK_FIVE_HTTP_ENDPOINTS';state='PASS';evidence='5/5 HTTP 200'},
        [ordered]@{step=7;name='VERIFY_SERVED_ROWS_AND_UNIQUE_IDS';state='PASS';evidence="rows=$servedRows unique=$uniqueRows status=$matrixRows summary=$candidateRows"},
        [ordered]@{step=8;name='FIND_INSTALLED_EDGE_OR_CHROME';state='PASS';evidence=$browser},
        [ordered]@{step=9;name='CAPTURE_PRECHECK_DOM';state='PASS';evidence=(Repo-Relative $precheck.dom_path)},
        [ordered]@{step=10;name='VERIFY_PRECHECK_100_PASS_0_FAIL';state='PASS';evidence="pass=$precheckPassRows fail=$precheckFailRows"},
        [ordered]@{step=11;name='DRIVE_CANONICAL_MATRIX_GAS_PAGES_1_TO_4';state='PASS';evidence='pages=4/4'},
        [ordered]@{step=12;name='AGGREGATE_EXACT_100_CANONICAL_DOM_ROWS';state='PASS';evidence="rows=$matrixAcceptanceRows unique=100"},
        [ordered]@{step=13;name='VERIFY_EXACT_28_SERIALIZED_HEADERS';state='PASS';evidence="headers=$matrixAcceptanceHeaders missing=$($missingHeaders.Count)"},
        [ordered]@{step=14;name='VERIFY_UNAMBIGUOUS_DOM_COMPLETION_MARKERS';state='PASS';evidence="complete=$matrixPassMarker pages=$matrixPageEvidence"},
        [ordered]@{step=15;name='CAPTURE_MATRIX_SCREENSHOT';state='PASS';evidence=$screenshot.path},
        [ordered]@{step=16;name='VERIFY_PNG_SIGNATURE_AND_1920X1080';state='PASS';evidence="$($screenshot.width)x$($screenshot.height)"},
        [ordered]@{step=17;name='HASH_SCREENSHOT_AND_STDERR';state='PASS';evidence=$screenshot.sha256},
        [ordered]@{step=18;name='CHECK_ALL_BROWSER_STDERR';state='PASS';evidence="script_errors=$($scriptErrors.Count) screenshot_errors=$($screenshot.stderr_error_markers)"},
        [ordered]@{step=19;name='REMOTE_PARITY_PHASE_TWO_AFTER_BROWSER';state='PASS';evidence=$remotePhaseAfter.current_remote_head},
        [ordered]@{step=20;name='VERIFY_WRAPPER_CARRIER_HARNESS_BLOBS_PHASE_TWO';state='PASS';evidence='3/3'},
        [ordered]@{step=21;name='WRITE_LOCAL_RESULT';state='PASS';evidence=(Repo-Relative $resultPath)},
        [ordered]@{step=22;name='COORDINATOR_SERIAL_PUBLISH';state='PENDING_COORDINATOR';evidence='No child direct push'},
        [ordered]@{step=23;name='REMOTE_COMMIT_READBACK';state='PENDING_COORDINATOR';evidence='Queue publisher must confirm remote readback'},
        [ordered]@{step=24;name='CHATGPT_FINAL_STATE_RECONCILIATION';state='PENDING_REMOTE_PROOF';evidence='Advance only after remote result readback'}
    )
    $status = [ordered]@{schema_version=11;slot_id=$slotId;updated_at=$generatedAt;status='COORDINATOR_V11_TWO_PHASE_REMOTE_PARITY_DOM_PNG_RUNTIME_PASS_AWAITING_SERIAL_REMOTE_PUBLISH_READBACK';runner_version=11;runner_policy='EXISTING_CANONICAL_F_SHARED_RUNNER_ONLY';steps=$steps;git=$gitEvidence;browser_path=$browser;git_executable=$gitExe;browser_dom_passed=$true;browser_acceptance_passed=$false;canonical_pages_verified=4;canonical_page_rows_verified=25;canonical_dom_rows_verified=100;canonical_dom_headers_verified=28;screenshot_captured=$true;screenshot_png_signature_passed=$true;screenshot_width=$screenshot.width;screenshot_height=$screenshot.height;screenshot_sha256=$screenshot.sha256;two_phase_remote_parity_passed=$true;coordinator_serial_publish_pending=$true;parcel_binding_gate_passed=$false;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
    Write-Json $status $statusPath
    if (Test-Path -LiteralPath $pickupPath -PathType Leaf) {
        $pickup = Get-Content -Raw -LiteralPath $pickupPath | ConvertFrom-Json
        foreach ($check in @($pickup.checks)) { if ([int]$check.row -eq 21 -or [int]$check.row -eq 22) { $check.actual=$true; $check.state='PASS_LOCAL_AWAITING_REMOTE_READBACK' } }
        $pickup.status='COORDINATOR_V11_TWO_PHASE_REMOTE_PARITY_DOM_PNG_RUNTIME_PASS_AWAITING_SERIAL_REMOTE_PUBLISH_READBACK';$pickup.runtime_checks_passed=1;$pickup.runtime_checks_total=2;$pickup.browser_dom_verified_rows=100;$pickup.browser_acceptance_passed=$false;$pickup.screenshot_captured=$true;$pickup.screenshot_png_signature_passed=$true;$pickup.screenshot_width=$screenshot.width;$pickup.screenshot_height=$screenshot.height;$pickup.two_phase_remote_parity_passed=$true;$pickup.updated_at=$generatedAt
        Write-Json $pickup $pickupPath
    }
    Write-Output "GAS_EMISSIONS_3_COORDINATOR_V11_RUNTIME_PASS PAGES=4 DOM=100 HEADERS=28 PNG=1920x1080 TWO_PHASE_REMOTE_PARITY=true SCREENSHOT_SHA256=$($screenshot.sha256) NEXT=COORDINATOR_SERIAL_PUBLISH_READBACK"
    exit 0
}
catch {
    $errorPayload = [ordered]@{schema_version=7;slot_id=$slotId;generated_at=[DateTime]::UtcNow.ToString('o');status='COORDINATOR_BROWSER_RUNTIME_BLOCKED';error=$_.Exception.Message;browser_dom_passed=$false;browser_acceptance_passed=$false;parcel_binding_gate_passed=$false;measured_parcel_values_produced=0;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
    Write-Json $errorPayload $resultPath
    Write-Json $errorPayload $statusPath
    throw
}
