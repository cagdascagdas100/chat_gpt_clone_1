[CmdletBinding()]
param(
    [int]$VirtualTimeBudgetMs = 45000,
    [int]$HttpTimeoutSeconds = 30
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

$precheckUrl = 'http://127.0.0.1:8012/england_map_web/data/aays_18_slots/gas_emissions_3/browser_acceptance_precheck.html?runner=coordinator-v7'
$matrixUrl = 'http://127.0.0.1:8012/england_map_web/data/aays_18_slots/gas_emissions_3/canonical_matrix_100_browser_harness.html?runner=coordinator-v7'
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
    $json = $Value | ConvertTo-Json -Depth 40
    $parent = Split-Path -Parent $Path
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [System.IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
}

function Invoke-Git([string[]]$GitArgs) {
    $output = & $gitExe -C $repoRoot @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) { throw "$gitExe $($GitArgs -join ' ') failed: $($output -join [Environment]::NewLine)" }
    return (($output -join [Environment]::NewLine).Trim())
}

function Get-RemoteHead {
    $raw = Invoke-Git @('ls-remote', 'origin', "refs/heads/$branch")
    if ([string]::IsNullOrWhiteSpace($raw)) { throw "Remote branch not found: $branch" }
    return ($raw -split '\s+')[0]
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
    foreach ($root in @(${env:ProgramFiles(x86)}, $env:ProgramFiles, $env:LOCALAPPDATA) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) {
        $candidates += (Join-Path $root 'Microsoft\Edge\Application\msedge.exe')
        $candidates += (Join-Path $root 'Google\Chrome\Application\chrome.exe')
    }
    $browser = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique | Select-Object -First 1
    if (-not $browser) { throw 'Installed Edge or Chrome executable was not found.' }
    return [string]$browser
}

function Invoke-DomDump([string]$Browser, [string]$Url, [string]$Label) {
    $profileDir = Join-Path $runtimeProofRoot ("profile_" + $Label)
    $stdoutPath = Join-Path $runtimeProofRoot ($Label + '_dom.html')
    $stderrPath = Join-Path $runtimeProofRoot ($Label + '_stderr.log')
    Remove-Item -Recurse -Force -LiteralPath $profileDir -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
    $arguments = @(
        '--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
        '--disable-background-networking','--disable-component-update',"--user-data-dir=$profileDir",
        "--virtual-time-budget=$VirtualTimeBudgetMs",'--dump-dom','--enable-logging=stderr','--log-level=3',$Url
    )
    & $Browser @arguments 1> $stdoutPath 2> $stderrPath
    $exitCode = $LASTEXITCODE
    $dom = if (Test-Path -LiteralPath $stdoutPath) { Get-Content -Raw -LiteralPath $stdoutPath } else { '' }
    $stderr = if (Test-Path -LiteralPath $stderrPath) { Get-Content -Raw -LiteralPath $stderrPath } else { '' }
    return [pscustomobject]@{
        label=$Label;url=$Url;exit_code=$exitCode;dom=$dom;stderr=$stderr;
        dom_path=$stdoutPath;stderr_path=$stderrPath;
        dom_sha256=if(Test-Path -LiteralPath $stdoutPath){(Get-FileHash -Algorithm SHA256 -LiteralPath $stdoutPath).Hash.ToLowerInvariant()}else{$null};
        stderr_sha256=if(Test-Path -LiteralPath $stderrPath){(Get-FileHash -Algorithm SHA256 -LiteralPath $stderrPath).Hash.ToLowerInvariant()}else{$null}
    }
}

function Capture-Screenshot([string]$Browser, [string]$Url) {
    $profileDir = Join-Path $runtimeProofRoot 'profile_screenshot'
    $stderrPath = Join-Path $runtimeProofRoot 'screenshot_stderr.log'
    Remove-Item -Recurse -Force -LiteralPath $profileDir -ErrorAction SilentlyContinue
    Remove-Item -Force -LiteralPath $screenshotPath -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
    $arguments = @(
        '--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
        '--disable-background-networking','--disable-component-update',"--user-data-dir=$profileDir",
        '--window-size=1920,1080',"--virtual-time-budget=$VirtualTimeBudgetMs",("--screenshot=" + $screenshotPath),$Url
    )
    & $Browser @arguments 1> $null 2> $stderrPath
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) { throw "Screenshot browser exited with code $exitCode" }
    if (-not (Test-Path -LiteralPath $screenshotPath -PathType Leaf)) { throw 'Screenshot file was not created.' }
    $info = Get-Item -LiteralPath $screenshotPath
    if ([int64]$info.Length -lt 10000) { throw "Screenshot file is unexpectedly small: $($info.Length) bytes" }
    return [ordered]@{
        status='PASS';url=$Url;canonical_matrix_url=$canonicalMatrixUrl;browser_path=$Browser;exit_code=$exitCode;
        path='docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/acceptance/013_gas_emissions_3_matrix_browser_screenshot_latest.png';
        byte_count=[int64]$info.Length;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $screenshotPath).Hash.ToLowerInvariant();
        stderr_path='docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/acceptance/020_coordinator_browser_runtime_latest/screenshot_stderr.log';
        captured_at=[DateTime]::UtcNow.ToString('o');remote_readback_required=$true
    }
}

function Count-Matches([string]$Text, [string]$Pattern) {
    if ([string]::IsNullOrEmpty($Text)) { return 0 }
    return [regex]::Matches($Text, $Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
}

function Repo-Relative([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($repoRoot,[StringComparison]::OrdinalIgnoreCase)) { throw "Path outside repository: $full" }
    return $full.Substring($repoRoot.Length).TrimStart('\').Replace('\','/')
}

try {
    if ([string]$env:AAYS_SLOT_ID -and [string]$env:AAYS_SLOT_ID -ne $slotId) { throw "AAYS_SLOT_ID mismatch: $env:AAYS_SLOT_ID" }
    if ([string]$env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN -ne 'true') { throw 'Coordinator child direct-push guard is not active.' }

    $localHead = Invoke-Git @('rev-parse','HEAD')
    $remoteHead = Get-RemoteHead
    if ($localHead -ne $remoteHead) { throw "Detached child HEAD does not match remote HEAD. local=$localHead remote=$remoteHead" }

    if (-not (Test-Path -LiteralPath $authoritativeCheckpointPath -PathType Leaf)) { throw "Authoritative checkpoint missing: $authoritativeCheckpointPath" }
    $authoritativeCheckpoint = Get-Content -Raw -LiteralPath $authoritativeCheckpointPath | ConvertFrom-Json
    if ($authoritativeCheckpoint.slot_id -ne $slotId) { throw 'Authoritative checkpoint slot mismatch.' }
    if ([int]$authoritativeCheckpoint.sequence -lt 19) { throw "Authoritative checkpoint sequence regressed: $($authoritativeCheckpoint.sequence)" }
    if (-not $runtimeCheckpointPath) { throw 'AAYS_PORTABLE_ROOT is required to preserve the coordinator runtime checkpoint.' }
    $runtimeCheckpoint = $authoritativeCheckpoint | Select-Object *
    $runtimeCheckpoint | Add-Member -NotePropertyName hydration_state -NotePropertyValue 'AUTHORITATIVE_REMOTE_SEQUENCE_PRESERVED_FOR_COORDINATOR_PUBLISH' -Force
    $runtimeCheckpoint | Add-Member -NotePropertyName updated_at -NotePropertyValue ([DateTime]::UtcNow.ToString('o')) -Force
    $runtimeCheckpoint | Add-Member -NotePropertyName remote_head -NotePropertyValue $remoteHead -Force
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
    $matrixPassMarker = $matrix.dom -match 'CANONICAL_MATRIX_AGGREGATED_BROWSER_PASS'
    $matrixPageEvidence = $matrix.dom -match 'pages=4/4' -and $matrix.dom -match 'unique=100/100'
    $matrixPassed = $matrix.exit_code -eq 0 -and $matrixPassMarker -and $matrixPageEvidence -and $matrixAcceptanceRows -eq 100 -and $missingHeaders.Count -eq 0

    $scriptErrors = @()
    foreach ($entry in @($precheck,$matrix)) {
        if ($entry.stderr -match '(?im)(uncaught|unhandled|javascript error|console[^`r`n]*error)') { $scriptErrors += "$($entry.label): browser stderr contains a script error marker" }
    }
    $browserDomPassed = $httpPassed -and $servedPassed -and $precheckPassed -and $matrixPassed -and $scriptErrors.Count -eq 0
    if (-not $browserDomPassed) { throw "Browser acceptance failed. http=$httpPassed served=$servedPassed precheck=$precheckPassed matrix=$matrixPassed matrix_rows=$matrixAcceptanceRows errors=$($scriptErrors.Count)" }

    $generatedAt = [DateTime]::UtcNow.ToString('o')
    $result = [ordered]@{
        schema_version=4;slot_id=$slotId;generated_at=$generatedAt;status='COORDINATOR_CANONICAL_4_PAGE_BROWSER_DOM_AND_SCREENSHOT_PASS_AWAITING_SERIAL_REMOTE_PUBLISH_READBACK';
        runner_policy='EXISTING_CANONICAL_F_SHARED_RUNNER_ONLY';runner_version=7;browser_path=$browser;git_executable=$gitExe;
        git=[ordered]@{local_head=$localHead;remote_head=$remoteHead;head_match=$true;direct_child_push_forbidden=$true;coordinator_serial_publish_required=$true;remote_publish_readback_passed=$false};
        http=[ordered]@{endpoint_count=5;all_status_200=$httpPassed;served_row_count=$servedRows;served_unique_row_count=$uniqueRows;matrix_status_row_count=$matrixRows;summary_candidate_count=$candidateRows;served_commit_sha=$matrixStatusHttp.json.served_commit_sha;served_commit_field_role='historical_informational_only_runtime_token_is_authoritative';passed=$servedPassed};
        precheck=[ordered]@{url=$precheckUrl;exit_code=$precheck.exit_code;pass_rows=$precheckPassRows;fail_rows=$precheckFailRows;dom_path=(Repo-Relative $precheck.dom_path);dom_sha256=$precheck.dom_sha256;stderr_path=(Repo-Relative $precheck.stderr_path);stderr_sha256=$precheck.stderr_sha256;passed=$precheckPassed};
        matrix=[ordered]@{harness_url=$matrixUrl;canonical_url=$canonicalMatrixUrl;exit_code=$matrix.exit_code;expected_pages=4;expected_rows=100;actual_dom_rows=$matrixAcceptanceRows;unique_rows=100;pass_marker_present=$matrixPassMarker;page_evidence_present=$matrixPageEvidence;required_header_count=$requiredHeaders.Count;missing_headers=$missingHeaders;dom_path=(Repo-Relative $matrix.dom_path);dom_sha256=$matrix.dom_sha256;stderr_path=(Repo-Relative $matrix.stderr_path);stderr_sha256=$matrix.stderr_sha256;passed=$matrixPassed};
        screenshot=$screenshot;browser_script_errors=$scriptErrors;browser_dom_passed=$true;browser_acceptance_passed=$false;coordinator_publish_required=$true;
        parcel_binding_gate_passed=$false;measured_parcel_values_produced=0;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false
    }
    Write-Json $result $resultPath

    $steps = @(
        [ordered]@{step=1;name='VALIDATE_DETACHED_CHILD_HEAD_EQUALS_REMOTE';state='PASS';evidence="local=$localHead remote=$remoteHead"},
        [ordered]@{step=2;name='USE_PORTABLE_GIT';state='PASS';evidence=$gitExe},
        [ordered]@{step=3;name='PRESERVE_AUTHORITATIVE_CHECKPOINT_SEQUENCE';state='PASS';evidence="sequence=$($authoritativeCheckpoint.sequence) runtime=$runtimeCheckpointPath"},
        [ordered]@{step=4;name='CHECK_FIVE_HTTP_ENDPOINTS';state='PASS';evidence='5/5 HTTP 200'},
        [ordered]@{step=5;name='VERIFY_SERVED_ROWS_AND_UNIQUE_IDS';state='PASS';evidence="rows=$servedRows unique=$uniqueRows status=$matrixRows summary=$candidateRows"},
        [ordered]@{step=6;name='FIND_INSTALLED_EDGE_OR_CHROME';state='PASS';evidence=$browser},
        [ordered]@{step=7;name='CAPTURE_PRECHECK_DOM';state='PASS';evidence=(Repo-Relative $precheck.dom_path)},
        [ordered]@{step=8;name='VERIFY_PRECHECK_100_PASS_0_FAIL';state='PASS';evidence="pass=$precheckPassRows fail=$precheckFailRows"},
        [ordered]@{step=9;name='DRIVE_CANONICAL_MATRIX_GAS_PAGES_1_TO_4';state='PASS';evidence='same-origin canonical iframe pages=4/4'},
        [ordered]@{step=10;name='AGGREGATE_EXACT_100_CANONICAL_DOM_ROWS';state='PASS';evidence="rows=$matrixAcceptanceRows unique=100"},
        [ordered]@{step=11;name='VERIFY_MATRIX_28_HEADERS';state='PASS';evidence="headers=$($requiredHeaders.Count) missing=$($missingHeaders.Count)"},
        [ordered]@{step=12;name='CAPTURE_MATRIX_SCREENSHOT';state='PASS';evidence=$screenshot.path},
        [ordered]@{step=13;name='HASH_SCREENSHOT_SHA256';state='PASS';evidence=$screenshot.sha256},
        [ordered]@{step=14;name='CHECK_BROWSER_STDERR';state='PASS';evidence="script_errors=$($scriptErrors.Count)"},
        [ordered]@{step=15;name='WRITE_LOCAL_RESULT';state='PASS';evidence=(Repo-Relative $resultPath)},
        [ordered]@{step=16;name='COORDINATOR_SERIAL_PUBLISH';state='PENDING_COORDINATOR';evidence='No child direct push'},
        [ordered]@{step=17;name='REMOTE_COMMIT_READBACK';state='PENDING_COORDINATOR';evidence='Queue publisher must confirm remote HEAD'},
        [ordered]@{step=18;name='CHATGPT_FINAL_STATE_RECONCILIATION';state='PENDING_REMOTE_PROOF';evidence='Advance summary/checkpoint only after remote result readback'}
    )
    $status = [ordered]@{
        schema_version=7;slot_id=$slotId;updated_at=$generatedAt;status='COORDINATOR_CANONICAL_4_PAGE_RUNTIME_PASS_AWAITING_SERIAL_REMOTE_PUBLISH_READBACK';runner_version=7;
        runner_policy='EXISTING_CANONICAL_F_SHARED_RUNNER_ONLY';steps=$steps;browser_path=$browser;git_executable=$gitExe;
        browser_dom_passed=$true;browser_acceptance_passed=$false;canonical_pages_verified=4;canonical_dom_rows_verified=100;screenshot_captured=$true;screenshot_sha256=$screenshot.sha256;
        coordinator_serial_publish_pending=$true;parcel_binding_gate_passed=$false;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false
    }
    Write-Json $status $statusPath

    if (Test-Path -LiteralPath $pickupPath -PathType Leaf) {
        $pickup = Get-Content -Raw -LiteralPath $pickupPath | ConvertFrom-Json
        foreach ($check in @($pickup.checks)) {
            if ([int]$check.row -eq 15 -or [int]$check.row -eq 16) { $check.actual=$true; $check.state='PASS_LOCAL_AWAITING_REMOTE_READBACK' }
        }
        $pickup.status='CANONICAL_4_PAGE_RUNTIME_PASS_AWAITING_COORDINATOR_SERIAL_REMOTE_PUBLISH_READBACK'
        $pickup.runtime_checks_passed=1
        $pickup.runtime_checks_total=2
        $pickup.browser_dom_verified_rows=100
        $pickup.browser_acceptance_passed=$false
        $pickup.screenshot_captured=$true
        $pickup.updated_at=$generatedAt
        Write-Json $pickup $pickupPath
    }

    Write-Output "GAS_EMISSIONS_3_COORDINATOR_RUNTIME_PASS PAGES=4 DOM=100 SCREENSHOT_SHA256=$($screenshot.sha256) NEXT=COORDINATOR_SERIAL_PUBLISH_READBACK"
    exit 0
}
catch {
    $errorPayload = [ordered]@{
        schema_version=4;slot_id=$slotId;generated_at=[DateTime]::UtcNow.ToString('o');status='COORDINATOR_BROWSER_RUNTIME_BLOCKED';
        error=$_.Exception.Message;browser_dom_passed=$false;browser_acceptance_passed=$false;parcel_binding_gate_passed=$false;
        measured_parcel_values_produced=0;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false
    }
    Write-Json $errorPayload $resultPath
    Write-Json $errorPayload $statusPath
    throw
}
