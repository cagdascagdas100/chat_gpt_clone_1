$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$logDir = Join-Path $projectRoot 'run_logs'
$traceLog = Join-Path $logDir 'run_uvicorn_8010.trace.log'
$stdoutLog = Join-Path $logDir 'uvicorn-8010.out.log'
$stderrLog = Join-Path $logDir 'uvicorn-8010.err.log'

$pythonCandidates = @(
  $env:AAYS_PYTHON_EXE,
  'C:\Python312\python.exe',
  'python'
) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

$pythonExe = $null
foreach ($candidate in $pythonCandidates) {
  if ($candidate -eq 'python') {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
      $pythonExe = 'python'
      break
    }
  } elseif (Test-Path -LiteralPath $candidate) {
    $pythonExe = $candidate
    break
  }
}

if (-not $pythonExe) {
  throw "Python executable not found. Set AAYS_PYTHON_EXE or install Python."
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
"START $(Get-Date -Format o)" | Out-File -FilePath $traceLog -Append -Encoding utf8
Set-Location $projectRoot
"PWD=$(Get-Location)" | Out-File -FilePath $traceLog -Append -Encoding utf8
"PYTHON=$pythonExe" | Out-File -FilePath $traceLog -Append -Encoding utf8

$listenerLine = (netstat -ano | Select-String ':8010\s+.*LISTENING' | Select-Object -First 1)
if ($listenerLine) {
  $parts = ($listenerLine.ToString() -split '\s+') | Where-Object { $_ -ne '' }
  $pidToken = $parts[-1]
  if ($pidToken -match '^\d+$') {
    "STOP_OLD_8010_PID=$pidToken" | Out-File -FilePath $traceLog -Append -Encoding utf8
    Stop-Process -Id ([int]$pidToken) -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 600
  }
}

"--- RUN $(Get-Date -Format o) ---" | Out-File -FilePath $stdoutLog -Append -Encoding utf8
"--- RUN $(Get-Date -Format o) ---" | Out-File -FilePath $stderrLog -Append -Encoding utf8

$dbPort = if ($env:TYLI_DB_PORT) { $env:TYLI_DB_PORT } else { '55460' }
$cmd = 'set "TYLI_DB_PORT={4}" && set "TYLI_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:{4}/terrayield_land" && cd /d "{0}" && "{1}" -m uvicorn app.main:app --host 127.0.0.1 --port 8010 1>> "{2}" 2>> "{3}"' -f $projectRoot, $pythonExe, $stdoutLog, $stderrLog, $dbPort
cmd.exe /d /c $cmd
$exitCode = $LASTEXITCODE
"EXITCODE=$exitCode" | Out-File -FilePath $traceLog -Append -Encoding utf8
"END $(Get-Date -Format o)" | Out-File -FilePath $traceLog -Append -Encoding utf8
exit $exitCode
