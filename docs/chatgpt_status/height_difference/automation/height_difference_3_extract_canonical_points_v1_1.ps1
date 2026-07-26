$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    $repoRoot = 'F:\chatgpt\chat_gpt_clone_1_main'
}

$scriptRelative = 'docs/chatgpt_status/height_difference/automation/height_difference_3_extract_canonical_points_v1_1.py'
$scriptPath = Join-Path $repoRoot $scriptRelative

if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
    Write-Error "Python extractor not found: $scriptPath"
    exit 2
}

Push-Location $repoRoot
try {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        & $python.Source $scriptPath
    }
    else {
        $py = Get-Command py -ErrorAction SilentlyContinue
        if ($null -eq $py) {
            Write-Error 'Neither python nor py command is available.'
            exit 2
        }
        & $py.Source -3 $scriptPath
    }
    $exitCode = $LASTEXITCODE
    Write-Host "HEIGHT_DIFFERENCE_3_EXTRACTOR_V1_1_EXIT_CODE=$exitCode"
    Write-Host 'FINAL_READY=false'
    exit $exitCode
}
finally {
    Pop-Location
}
