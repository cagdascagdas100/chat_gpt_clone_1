$projectRoot = $PSScriptRoot
$runner = Join-Path $projectRoot 'run_uvicorn_8010.ps1'

if (-not (Test-Path -LiteralPath $runner)) {
  throw "Missing script: $runner"
}

$proc = Start-Process -FilePath powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$runner) -WindowStyle Hidden -PassThru
"launcher_pid=$($proc.Id)"
Start-Sleep -Seconds 3
$listen = netstat -ano | Select-String ':8010\s+.*LISTENING' | Select-Object -First 1
if ($listen) {
  "status=listening"
  $listen.ToString().Trim()
} else {
  "status=starting_or_failed"
}
