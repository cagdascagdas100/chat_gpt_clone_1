[CmdletBinding()]
param(
    [string]$RepoRoot = $env:AAYS_REPO_ROOT,
    [string]$MatrixUrl = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=gas100&standalone=1',
    [int]$VirtualTimeBudgetMs = 25000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..\..')).Path
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path.TrimEnd('\')
$acceptanceRoot = Join-Path $RepoRoot 'docs\chatgpt_status\gas_emissions\shards\gas_emissions_3\acceptance'
$screenshotPath = Join-Path $acceptanceRoot '013_gas_emissions_3_matrix_browser_screenshot_latest.png'
$metadataPath = Join-Path $acceptanceRoot '013_gas_emissions_3_matrix_browser_screenshot_latest.json'
New-Item -ItemType Directory -Force -Path $acceptanceRoot | Out-Null

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
    return $browser
}

function Get-RepoRelativePath([string]$AbsolutePath) {
    $full = [IO.Path]::GetFullPath($AbsolutePath)
    if (-not $full.StartsWith($RepoRoot,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside repository: $full"
    }
    return $full.Substring($RepoRoot.Length).TrimStart('\').Replace('\','/')
}

function Write-Json($Value,[string]$Path) {
    $json = $Value | ConvertTo-Json -Depth 16
    [IO.File]::WriteAllText($Path,$json,[Text.UTF8Encoding]::new($false))
}

$runRoot = Join-Path $env:TEMP ('aays-gas-emissions-3-screenshot-' + [guid]::NewGuid().ToString('N'))
$profileDir = Join-Path $runRoot 'profile'
$stderrPath = Join-Path $runRoot 'stderr.log'
New-Item -ItemType Directory -Force -Path $profileDir | Out-Null

try {
    Remove-Item -LiteralPath $screenshotPath -Force -ErrorAction SilentlyContinue
    $browser = Find-Browser
    $arguments = @(
        '--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
        '--disable-background-networking','--disable-component-update','--hide-scrollbars',
        '--window-size=1920,1080',"--user-data-dir=$profileDir",
        "--virtual-time-budget=$VirtualTimeBudgetMs","--screenshot=$screenshotPath",$MatrixUrl
    )
    & $browser @arguments 1>$null 2>$stderrPath
    $exitCode = $LASTEXITCODE
    $stderr = if (Test-Path -LiteralPath $stderrPath) { Get-Content -Raw -LiteralPath $stderrPath } else { '' }
    $scriptError = $stderr -match '(?im)(uncaught|unhandled|javascript error|console[^`r`n]*error)'
    $exists = Test-Path -LiteralPath $screenshotPath -PathType Leaf
    $bytes = if ($exists) { (Get-Item -LiteralPath $screenshotPath).Length } else { 0 }
    $sha256 = if ($exists -and $bytes -gt 0) { (Get-FileHash -Algorithm SHA256 -LiteralPath $screenshotPath).Hash.ToLowerInvariant() } else { $null }
    $passed = $exitCode -eq 0 -and $exists -and $bytes -gt 0 -and -not $scriptError -and -not [string]::IsNullOrWhiteSpace($sha256)
    $payload = [ordered]@{
        schema_version=1
        slot_id='gas_emissions_3'
        generated_at=[DateTime]::UtcNow.ToString('o')
        status=if($passed){'SCREENSHOT_PASS_LOCAL_AWAITING_REMOTE_LEDGER'}else{'SCREENSHOT_FAIL'}
        runner_policy='EXISTING_CANONICAL_F_SHARED_RUNNER_ONLY'
        browser_path=$browser
        matrix_url=$MatrixUrl
        screenshot_path=Get-RepoRelativePath $screenshotPath
        screenshot_sha256=$sha256
        screenshot_bytes=$bytes
        browser_exit_code=$exitCode
        stderr_script_error=$scriptError
        passed=$passed
        browser_acceptance_passed=$false
        parcel_binding_gate_passed=$false
        final_ready=$false
        fake_data=$false
        db_write=$false
        migration=$false
        production_deploy=$false
    }
    Write-Json $payload $metadataPath
    if (-not $passed) { exit 2 }
    Write-Output "SCREENSHOT_PASS SLOT_ID=gas_emissions_3 PATH=$($payload.screenshot_path) SHA256=$sha256 BYTES=$bytes"
    exit 0
}
catch {
    $payload = [ordered]@{
        schema_version=1;slot_id='gas_emissions_3';generated_at=[DateTime]::UtcNow.ToString('o');status='SCREENSHOT_ERROR';error=$_.Exception.Message
        runner_policy='EXISTING_CANONICAL_F_SHARED_RUNNER_ONLY';passed=$false;browser_acceptance_passed=$false;parcel_binding_gate_passed=$false
        final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false
    }
    Write-Json $payload $metadataPath
    throw
}
finally {
    if (Test-Path -LiteralPath $runRoot) { Remove-Item -Recurse -Force -LiteralPath $runRoot -ErrorAction SilentlyContinue }
}
