[CmdletBinding()]
param(
    [string]$RepoRoot = $env:AAYS_REPO_ROOT,
    [string]$Branch = 'codex/aays-single-runner-v5-20260706',
    [int]$VirtualTimeBudgetMs = 20000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..\..')).Path
}

$slotId = 'gas_emissions_3'
$siteRoot = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3'
$acceptanceRoot = Join-Path $RepoRoot 'docs\chatgpt_status\gas_emissions\shards\gas_emissions_3\acceptance'
$precheckUrl = 'http://127.0.0.1:8012/england_map_web/data/aays_18_slots/gas_emissions_3/browser_acceptance_precheck.html?runner=canonical'
$matrixUrl = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=gas100&standalone=1'
$statusPath = Join-Path $siteRoot 'browser_acceptance_runner_status_latest.json'
$resultPath = Join-Path $acceptanceRoot '012_gas_emissions_3_100_browser_acceptance_local_result_latest.json'
New-Item -ItemType Directory -Force -Path $siteRoot, $acceptanceRoot | Out-Null

function Find-Browser {
    $candidates = @()
    foreach ($name in @('msedge.exe','msedge','chrome.exe','chrome')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) { $candidates += $command.Source }
    }
    $candidates += @(
        (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'),
        (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
        (Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe')
    )
    $browser = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    if (-not $browser) { throw 'Installed Edge or Chrome executable was not found.' }
    return $browser
}

function Invoke-DomDump {
    param([string]$Browser,[string]$Url,[string]$Label)
    $runId = [guid]::NewGuid().ToString('N')
    $workDir = Join-Path $env:TEMP "aays-$slotId-$Label-$runId"
    $profileDir = Join-Path $workDir 'profile'
    $stdoutPath = Join-Path $workDir 'stdout.html'
    $stderrPath = Join-Path $workDir 'stderr.log'
    New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
    $arguments = @('--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update',"--user-data-dir=$profileDir","--virtual-time-budget=$VirtualTimeBudgetMs",'--dump-dom','--enable-logging=stderr','--log-level=3',$Url)
    & $Browser @arguments 1> $stdoutPath 2> $stderrPath
    $exitCode = $LASTEXITCODE
    $dom = if (Test-Path $stdoutPath) { Get-Content -Raw -LiteralPath $stdoutPath } else { '' }
    $stderr = if (Test-Path $stderrPath) { Get-Content -Raw -LiteralPath $stderrPath } else { '' }
    [pscustomobject]@{Label=$Label;Url=$Url;ExitCode=$exitCode;Dom=$dom;Stderr=$stderr;WorkDir=$workDir}
}

function Count-Matches([string]$Text,[string]$Pattern) {
    if ([string]::IsNullOrEmpty($Text)) { return 0 }
    return [regex]::Matches($Text,$Pattern,[System.Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
}

function Write-Json($Value,[string]$Path) {
    $json = $Value | ConvertTo-Json -Depth 12
    [System.IO.File]::WriteAllText($Path,$json,[System.Text.UTF8Encoding]::new($false))
}

$browserPath = $null
$precheck = $null
$matrix = $null
try {
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
        if ($entry.Stderr -match '(?im)(uncaught|unhandled|javascript error|console[^`r`n]*error)') { $browserScriptErrors += "$($entry.Label): browser stderr contains a script error marker" }
    }

    $precheckPassed = $precheck.ExitCode -eq 0 -and $precheckStatusPresent -and $precheckMachineResultPresent -and $precheckPassRows -eq 100 -and $precheckFailRows -eq 0
    $matrixPassed = $matrix.ExitCode -eq 0 -and $matrixHundredRowsPresent -and $matrixPageInfoPresent -and $missingHeaders.Count -eq 0
    $browserDomPassed = $precheckPassed -and $matrixPassed -and $browserScriptErrors.Count -eq 0

    $result = [ordered]@{
        schema_version=1;slot_id=$slotId;generated_at=[DateTime]::UtcNow.ToString('o');branch=$Branch
        status=if($browserDomPassed){'LOCAL_BROWSER_DOM_PASS_AWAITING_COMMIT_PUSH_REMOTE_READBACK'}else{'LOCAL_BROWSER_DOM_FAIL'}
        runner_policy='EXISTING_CANONICAL_F_SHARED_RUNNER_ONLY';browser_path=$browserPath
        precheck=[ordered]@{url=$precheckUrl;exit_code=$precheck.ExitCode;pass_rows=$precheckPassRows;fail_rows=$precheckFailRows;status_present=$precheckStatusPresent;machine_result_present=$precheckMachineResultPresent;passed=$precheckPassed}
        matrix=[ordered]@{url=$matrixUrl;exit_code=$matrix.ExitCode;expected_rows=100;hundred_rows_text_present=$matrixHundredRowsPresent;page_info_100_present=$matrixPageInfoPresent;required_header_count=$requiredHeaders.Count;missing_headers=$missingHeaders;passed=$matrixPassed}
        browser_script_errors=$browserScriptErrors;browser_dom_passed=$browserDomPassed;browser_acceptance_passed=$false;remote_commit_push_readback_required=$true
        parcel_binding_gate_passed=$false;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false
    }
    Write-Json $result $resultPath

    $siteStatus = [ordered]@{
        schema_version=1;slot_id=$slotId;updated_at=$result.generated_at;status=$result.status;runner_policy=$result.runner_policy
        script_path='docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/acceptance/run_gas_emissions_3_100_browser_acceptance.ps1';browser_path=$browserPath
        steps=@(
            [ordered]@{step=1;name='FIND_EXISTING_EDGE_OR_CHROME';state='PASS'},
            [ordered]@{step=2;name='DUMP_PRECHECK_DOM_WITH_JAVASCRIPT';state=if($precheck.ExitCode -eq 0){'PASS'}else{'FAIL'}},
            [ordered]@{step=3;name='VERIFY_100_PRECHECK_PASS_ROWS';state=if($precheckPassed){'PASS'}else{'FAIL'}},
            [ordered]@{step=4;name='DUMP_CANONICAL_MATRIX_DOM_WITH_JAVASCRIPT';state=if($matrix.ExitCode -eq 0){'PASS'}else{'FAIL'}},
            [ordered]@{step=5;name='VERIFY_MATRIX_100_ROWS_AND_REQUIRED_HEADERS';state=if($matrixPassed){'PASS'}else{'FAIL'}},
            [ordered]@{step=6;name='CHECK_BROWSER_STDERR_FOR_SCRIPT_ERRORS';state=if($browserScriptErrors.Count -eq 0){'PASS'}else{'FAIL'}},
            [ordered]@{step=7;name='WRITE_LOCAL_BROWSER_PROOF_JSON';state='PASS'},
            [ordered]@{step=8;name='COMMIT_PUSH_REMOTE_READBACK_ON_EXISTING_RUNNER';state='PENDING'}
        )
        precheck_pass_rows=$precheckPassRows;precheck_fail_rows=$precheckFailRows;matrix_expected_rows=100;matrix_100_rows_present=$matrixHundredRowsPresent;missing_header_count=$missingHeaders.Count
        browser_dom_passed=$browserDomPassed;browser_acceptance_passed=$false;parcel_binding_gate_passed=$false;final_ready=$false
    }
    Write-Json $siteStatus $statusPath
    if (-not $browserDomPassed) { exit 2 }
    exit 0
}
catch {
    $errorResult = [ordered]@{schema_version=1;slot_id=$slotId;generated_at=[DateTime]::UtcNow.ToString('o');status='RUNNER_ERROR';error=$_.Exception.Message;runner_policy='EXISTING_CANONICAL_F_SHARED_RUNNER_ONLY';browser_dom_passed=$false;browser_acceptance_passed=$false;parcel_binding_gate_passed=$false;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
    Write-Json $errorResult $resultPath
    Write-Json $errorResult $statusPath
    throw
}
finally {
    foreach ($entry in @($precheck,$matrix)) {
        if ($entry -and $entry.WorkDir -and (Test-Path $entry.WorkDir)) { Remove-Item -Recurse -Force -LiteralPath $entry.WorkDir -ErrorAction SilentlyContinue }
    }
}
