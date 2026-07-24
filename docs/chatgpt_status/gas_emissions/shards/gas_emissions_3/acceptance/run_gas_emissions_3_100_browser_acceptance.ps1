[CmdletBinding()]
param(
    [string]$RepoRoot = $env:AAYS_REPO_ROOT,
    [string]$Branch = 'codex/aays-single-runner-v5-20260706',
    [int]$VirtualTimeBudgetMs = 25000,
    [int]$HttpTimeoutSeconds = 30,
    [switch]$PublishProof
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..\..')).Path
}
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
    throw "Repo root not found: $RepoRoot"
}

$slotId = 'gas_emissions_3'
$siteRoot = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3'
$acceptanceRoot = Join-Path $RepoRoot 'docs\chatgpt_status\gas_emissions\shards\gas_emissions_3\acceptance'
$precheckUrl = 'http://127.0.0.1:8012/england_map_web/data/aays_18_slots/gas_emissions_3/browser_acceptance_precheck.html?runner=canonical-v2'
$matrixUrl = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=gas100&standalone=1'
$visibleRowsUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json'
$matrixStatusUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json'
$shardSummaryUrl = 'http://127.0.0.1:8012/england_map_web/data/aays_18_slots/gas_emissions_3/summary_latest.json'
$statusPath = Join-Path $siteRoot 'browser_acceptance_runner_status_latest.json'
$resultPath = Join-Path $acceptanceRoot '012_gas_emissions_3_100_browser_acceptance_local_result_latest.json'
New-Item -ItemType Directory -Force -Path $siteRoot, $acceptanceRoot | Out-Null

function Write-Json($Value, [string]$Path) {
    $json = $Value | ConvertTo-Json -Depth 16
    [System.IO.File]::WriteAllText($Path, $json, [System.Text.UTF8Encoding]::new($false))
}

function Invoke-Git([string[]]$GitArgs) {
    $output = & git -C $RepoRoot @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    return (($output -join [Environment]::NewLine).Trim())
}

function Get-RemoteHead {
    $raw = Invoke-Git @('ls-remote', 'origin', "refs/heads/$Branch")
    if ([string]::IsNullOrWhiteSpace($raw)) { throw "Remote branch not found: $Branch" }
    return ($raw -split '\s+')[0]
}

function Invoke-HttpText([string]$Url) {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $HttpTimeoutSeconds -Headers @{'Cache-Control'='no-cache'}
    [pscustomobject]@{Url=$Url;StatusCode=[int]$response.StatusCode;Content=[string]$response.Content;Passed=([int]$response.StatusCode -eq 200)}
}

function Invoke-HttpJson([string]$Url) {
    $text = Invoke-HttpText $Url
    $json = $text.Content | ConvertFrom-Json
    [pscustomobject]@{Url=$Url;StatusCode=$text.StatusCode;Content=$text.Content;Json=$json;Passed=$text.Passed}
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
    $browser = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique | Select-Object -First 1
    if (-not $browser) { throw 'Installed Edge or Chrome executable was not found.' }
    return $browser
}

function Invoke-DomDump {
    param([string]$Browser, [string]$Url, [string]$Label)
    $runId = [guid]::NewGuid().ToString('N')
    $workDir = Join-Path $env:TEMP "aays-$slotId-$Label-$runId"
    $profileDir = Join-Path $workDir 'profile'
    $stdoutPath = Join-Path $workDir 'stdout.html'
    $stderrPath = Join-Path $workDir 'stderr.log'
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
    [pscustomobject]@{Label=$Label;Url=$Url;ExitCode=$exitCode;Dom=$dom;Stderr=$stderr;WorkDir=$workDir}
}

function Count-Matches([string]$Text, [string]$Pattern) {
    if ([string]::IsNullOrEmpty($Text)) { return 0 }
    return [regex]::Matches($Text, $Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
}

function New-Step([int]$Number, [string]$Name, [string]$State, [string]$Evidence) {
    [ordered]@{step=$Number;name=$Name;state=$State;evidence=$Evidence}
}

$browserPath = $null
$precheck = $null
$matrix = $null
$proofRemoteReadbackPassed = $false
try {
    $localBranch = Invoke-Git @('rev-parse','--abbrev-ref','HEAD')
    $localHeadBefore = Invoke-Git @('rev-parse','HEAD')
    $remoteHeadBefore = Get-RemoteHead
    $branchPassed = $localBranch -eq $Branch
    if (-not $branchPassed) { throw "Active branch mismatch. Expected $Branch, found $localBranch" }

    $precheckHttp = Invoke-HttpText $precheckUrl
    $matrixHttp = Invoke-HttpText $matrixUrl
    $visibleRowsHttp = Invoke-HttpJson $visibleRowsUrl
    $matrixStatusHttp = Invoke-HttpJson $matrixStatusUrl
    $shardSummaryHttp = Invoke-HttpJson $shardSummaryUrl

    $visibleRows = @($visibleRowsHttp.Json.rows)
    $servedRowCount = $visibleRows.Count
    $servedUniqueRowCount = @($visibleRows | ForEach-Object { $_.row_id } | Sort-Object -Unique).Count
    $matrixStatusRowCount = [int]$matrixStatusHttp.Json.visible_rows_count
    $summaryCandidateCount = [int]$shardSummaryHttp.Json.metrics.revision_candidates
    $httpEndpointsPassed = @($precheckHttp,$matrixHttp,$visibleRowsHttp,$matrixStatusHttp,$shardSummaryHttp).Where({$_.Passed}).Count -eq 5
    $servedDataPassed = $servedRowCount -eq 100 -and $servedUniqueRowCount -eq 100 -and $matrixStatusRowCount -eq 100 -and $summaryCandidateCount -eq 100

    $browserPath = Find-Browser
    $precheck = Invoke-DomDump -Browser $browserPath -Url $precheckUrl -Label 'precheck'
    $matrix = Invoke-DomDump -Browser $browserPath -Url $matrixUrl -Label 'matrix'

    $precheckPassRows = Count-Matches $precheck.Dom '<tr[^>]*class=["'']pass["'']'
    $precheckFailRows = Count-Matches $precheck.Dom '<tr[^>]*class=["'']fail["'']'
    $precheckStatusPresent = $precheck.Dom -match 'PRECHECK_PASS_NOT_BROWSER_ACCEPTANCE'
    $precheckMachineResultPresent = $precheck.Dom -match '__gasEmissions3Precheck|machine'

    $requiredHeaders = @('Durum','Satır','Yıl','Sektör','Alt sektör','Sera gazı','Emisyon \(kt CO2e\)','Etki alanı \(kt CO2\)','Kaynak satırı','Eşleştirme yöntemi','Hesap açıklaması','Parcel binding','Güven \(%\)','Doğruluk','Resmi kaynak URL','Ham yerel kaynak','Visible artifact','Status yolu','Rapor yolu','Served commit','Artifact SHA','Manuel inceleme','Resmi CSV eşleşmesi','Kaynak SHA-256','Kaynak manifesti','Satır kanıtı','Pipeline','Blocker')
    $missingHeaders = @($requiredHeaders | Where-Object { $matrix.Dom -notmatch $_ })
    $matrixHundredRowsPresent = $matrix.Dom -match '(?i)(100\s*satır|100\s*rows)'
    $matrixPageInfoPresent = $matrix.Dom -match '(?i)Sayfa\s+1\s*/\s*[0-9]+\s*-\s*100\s*satır'
    $browserScriptErrors = @()
    foreach ($entry in @($precheck,$matrix)) {
        if ($entry.Stderr -match '(?im)(uncaught|unhandled|javascript error|console[^`r`n]*error)') {
            $browserScriptErrors += "$($entry.Label): browser stderr contains a script error marker"
        }
    }

    $precheckPassed = $precheck.ExitCode -eq 0 -and $precheckStatusPresent -and $precheckMachineResultPresent -and $precheckPassRows -eq 100 -and $precheckFailRows -eq 0
    $matrixPassed = $matrix.ExitCode -eq 0 -and $matrixHundredRowsPresent -and $matrixPageInfoPresent -and $missingHeaders.Count -eq 0
    $browserDomPassed = $httpEndpointsPassed -and $servedDataPassed -and $precheckPassed -and $matrixPassed -and $browserScriptErrors.Count -eq 0

    $result = [ordered]@{
        schema_version=2;slot_id=$slotId;generated_at=[DateTime]::UtcNow.ToString('o');branch=$Branch
        status=if($browserDomPassed){'LOCAL_BROWSER_DOM_PASS_AWAITING_COMMIT_PUSH_REMOTE_READBACK'}else{'LOCAL_BROWSER_DOM_FAIL'}
        runner_policy='EXISTING_CANONICAL_F_SHARED_RUNNER_ONLY';browser_path=$browserPath
        git=[ordered]@{local_branch=$localBranch;local_head_before=$localHeadBefore;remote_head_before=$remoteHeadBefore;branch_passed=$branchPassed;publish_requested=[bool]$PublishProof;proof_remote_readback_passed=$false}
        http=[ordered]@{endpoint_count=5;all_status_200=$httpEndpointsPassed;served_row_count=$servedRowCount;served_unique_row_count=$servedUniqueRowCount;matrix_status_row_count=$matrixStatusRowCount;shard_summary_candidate_count=$summaryCandidateCount;served_data_passed=$servedDataPassed;served_commit_sha=$matrixStatusHttp.Json.served_commit_sha}
        precheck=[ordered]@{url=$precheckUrl;exit_code=$precheck.ExitCode;pass_rows=$precheckPassRows;fail_rows=$precheckFailRows;status_present=$precheckStatusPresent;machine_result_present=$precheckMachineResultPresent;passed=$precheckPassed}
        matrix=[ordered]@{url=$matrixUrl;exit_code=$matrix.ExitCode;expected_rows=100;hundred_rows_text_present=$matrixHundredRowsPresent;page_info_100_present=$matrixPageInfoPresent;required_header_count=$requiredHeaders.Count;missing_headers=$missingHeaders;passed=$matrixPassed}
        browser_script_errors=$browserScriptErrors;browser_dom_passed=$browserDomPassed;browser_acceptance_passed=$false;remote_commit_push_readback_required=$true
        parcel_binding_gate_passed=$false;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false
    }

    $steps = @(
        (New-Step 1 'VALIDATE_REPO_ROOT' 'PASS' $RepoRoot),
        (New-Step 2 'VALIDATE_ACTIVE_BRANCH_AND_REMOTE_HEAD' 'PASS' "branch=$localBranch local=$localHeadBefore remote=$remoteHeadBefore"),
        (New-Step 3 'CHECK_PORT_8012_HTTP_ENDPOINTS' $(if($httpEndpointsPassed){'PASS'}else{'FAIL'}) '5 required HTTP endpoints'),
        (New-Step 4 'VERIFY_SERVED_100_ROWS_AND_100_UNIQUE_IDS' $(if($servedDataPassed){'PASS'}else{'FAIL'}) "rows=$servedRowCount unique=$servedUniqueRowCount status=$matrixStatusRowCount summary=$summaryCandidateCount"),
        (New-Step 5 'FIND_EXISTING_EDGE_OR_CHROME' 'PASS' $browserPath),
        (New-Step 6 'DUMP_PRECHECK_DOM_WITH_JAVASCRIPT' $(if($precheck.ExitCode -eq 0){'PASS'}else{'FAIL'}) "exit=$($precheck.ExitCode)"),
        (New-Step 7 'VERIFY_100_PRECHECK_PASS_ROWS' $(if($precheckPassed){'PASS'}else{'FAIL'}) "pass=$precheckPassRows fail=$precheckFailRows"),
        (New-Step 8 'DUMP_CANONICAL_MATRIX_DOM_WITH_JAVASCRIPT' $(if($matrix.ExitCode -eq 0){'PASS'}else{'FAIL'}) "exit=$($matrix.ExitCode)"),
        (New-Step 9 'VERIFY_MATRIX_100_ROWS_AND_28_HEADERS' $(if($matrixPassed){'PASS'}else{'FAIL'}) "missing_headers=$($missingHeaders.Count)"),
        (New-Step 10 'CHECK_BROWSER_STDERR_FOR_SCRIPT_ERRORS' $(if($browserScriptErrors.Count -eq 0){'PASS'}else{'FAIL'}) "errors=$($browserScriptErrors.Count)"),
        (New-Step 11 'WRITE_LOCAL_BROWSER_PROOF_JSON' 'PASS' $resultPath),
        (New-Step 12 'COMMIT_PUSH_REMOTE_READBACK_ON_EXISTING_RUNNER' $(if($PublishProof){'PENDING'}else{'NOT_REQUESTED'}) 'Requires browser DOM pass and -PublishProof')
    )

    $siteStatus = [ordered]@{
        schema_version=2;slot_id=$slotId;updated_at=$result.generated_at;status=$result.status;runner_policy=$result.runner_policy;runner_version=2
        script_path='docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/acceptance/run_gas_emissions_3_100_browser_acceptance.ps1';browser_path=$browserPath
        target=[ordered]@{precheck_url=$precheckUrl;matrix_url=$matrixUrl;visible_rows_url=$visibleRowsUrl;matrix_status_url=$matrixStatusUrl;expected_precheck_rows=100;expected_matrix_rows=100;last_proven_matrix_rows=66}
        steps=$steps;http_endpoints_passed=$httpEndpointsPassed;served_row_count=$servedRowCount;served_unique_row_count=$servedUniqueRowCount;matrix_status_row_count=$matrixStatusRowCount
        precheck_pass_rows=$precheckPassRows;precheck_fail_rows=$precheckFailRows;missing_header_count=$missingHeaders.Count
        browser_dom_passed=$browserDomPassed;browser_acceptance_passed=$false;parcel_binding_gate_passed=$false;final_ready=$false
    }
    Write-Json $result $resultPath
    Write-Json $siteStatus $statusPath

    if ($browserDomPassed -and $PublishProof) {
        $relativeResult = [IO.Path]::GetRelativePath($RepoRoot, $resultPath).Replace('\','/')
        $relativeStatus = [IO.Path]::GetRelativePath($RepoRoot, $statusPath).Replace('\','/')
        Invoke-Git @('add','--',$relativeResult,$relativeStatus) | Out-Null
        $commitOutput = & git -C $RepoRoot commit -m 'gas_emissions_3: record local 100-row browser DOM proof' 2>&1
        if ($LASTEXITCODE -ne 0 -and ($commitOutput -join ' ') -notmatch 'nothing to commit') { throw ($commitOutput -join [Environment]::NewLine) }
        Invoke-Git @('push','origin',$Branch) | Out-Null
        $proofCommit = Invoke-Git @('rev-parse','HEAD')
        $proofRemoteHead = Get-RemoteHead
        $proofRemoteReadbackPassed = $proofCommit -eq $proofRemoteHead
        $result.git.proof_commit = $proofCommit
        $result.git.proof_remote_head = $proofRemoteHead
        $result.git.proof_remote_readback_passed = $proofRemoteReadbackPassed
        $result.browser_acceptance_passed = $proofRemoteReadbackPassed
        $result.status = if($proofRemoteReadbackPassed){'BROWSER_100_ACCEPTANCE_PASS_REMOTE_PROOF_READBACK'}else{'BROWSER_DOM_PASS_REMOTE_READBACK_FAIL'}
        $siteStatus.status = $result.status
        $siteStatus.browser_acceptance_passed = $result.browser_acceptance_passed
        $siteStatus.steps[11].state = if($proofRemoteReadbackPassed){'PASS'}else{'FAIL'}
        $siteStatus.steps[11].evidence = "local=$proofCommit remote=$proofRemoteHead"
        Write-Json $result $resultPath
        Write-Json $siteStatus $statusPath
        Invoke-Git @('add','--',$relativeResult,$relativeStatus) | Out-Null
        $statusCommitOutput = & git -C $RepoRoot commit -m 'gas_emissions_3: record browser proof remote readback' 2>&1
        if ($LASTEXITCODE -ne 0 -and ($statusCommitOutput -join ' ') -notmatch 'nothing to commit') { throw ($statusCommitOutput -join [Environment]::NewLine) }
        Invoke-Git @('push','origin',$Branch) | Out-Null
        $finalLocalHead = Invoke-Git @('rev-parse','HEAD')
        $finalRemoteHead = Get-RemoteHead
        if ($finalLocalHead -ne $finalRemoteHead) { throw "Final remote readback failed: local=$finalLocalHead remote=$finalRemoteHead" }
    }

    if (-not $browserDomPassed) { exit 2 }
    if ($PublishProof -and -not $proofRemoteReadbackPassed) { exit 3 }
    exit 0
}
catch {
    $errorResult = [ordered]@{schema_version=2;slot_id=$slotId;generated_at=[DateTime]::UtcNow.ToString('o');status='RUNNER_ERROR';error=$_.Exception.Message;runner_policy='EXISTING_CANONICAL_F_SHARED_RUNNER_ONLY';browser_dom_passed=$false;browser_acceptance_passed=$false;parcel_binding_gate_passed=$false;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
    Write-Json $errorResult $resultPath
    Write-Json $errorResult $statusPath
    throw
}
finally {
    foreach ($entry in @($precheck,$matrix)) {
        if ($entry -and $entry.WorkDir -and (Test-Path -LiteralPath $entry.WorkDir)) {
            Remove-Item -Recurse -Force -LiteralPath $entry.WorkDir -ErrorAction SilentlyContinue
        }
    }
}
