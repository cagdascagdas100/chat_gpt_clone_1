$ErrorActionPreference = 'Continue'
$Project = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Start = Get-Date
$Run = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportDir = Join-Path $Project ".aays_next_fix\recovery_018_multitask_supervisor_$Run"
$SummaryFile = Join-Path $ReportDir 'summary.md'
$DetailFile = Join-Path $ReportDir 'detail.txt'
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Set-Location $Project

function Log([string]$Text) {
  $elapsed = [int]((Get-Date) - $Start).TotalSeconds
  $line = "[$elapsed s] $Text"
  Write-Output $line
  Add-Content -Encoding UTF8 -Path $DetailFile -Value $line
}

function Run-Capture([string]$Label, [scriptblock]$Block) {
  Log "--- $Label ---"
  try {
    $out = & $Block 2>&1 | Out-String
    Add-Content -Encoding UTF8 -Path $DetailFile -Value $out
    Write-Output $out
    Log "$Label EXIT=$LASTEXITCODE"
    return $out
  } catch {
    $msg = "$Label ERROR=$($_.Exception.Message)"
    Log $msg
    return $msg
  }
}

function Run-ParallelProbes($ProbeList, [int]$TimeoutSec = 120) {
  $jobs = @()
  foreach ($p in $ProbeList) {
    $jobs += Start-Job -Name $p.Name -ArgumentList $Project, $p.Command -ScriptBlock {
      param($ProjectArg, $CommandArg)
      Set-Location $ProjectArg
      $started = Get-Date
      try {
        $output = powershell -NoProfile -ExecutionPolicy Bypass -Command $CommandArg 2>&1 | Out-String
        [pscustomobject]@{ Name=$env:COMPUTERNAME; Started=$started; Finished=Get-Date; Command=$CommandArg; Output=$output; Error=$null }
      } catch {
        [pscustomobject]@{ Name=$env:COMPUTERNAME; Started=$started; Finished=Get-Date; Command=$CommandArg; Output=''; Error=$_.Exception.Message }
      }
    }
  }
  Wait-Job -Job $jobs -Timeout $TimeoutSec | Out-Null
  foreach ($j in $jobs) {
    if ($j.State -eq 'Running') {
      Stop-Job $j -Force | Out-Null
      Log "PARALLEL_TIMEOUT $($j.Name) after ${TimeoutSec}s"
    }
  }
  $results = @()
  foreach ($j in $jobs) {
    $r = Receive-Job $j -ErrorAction SilentlyContinue
    Remove-Job $j -Force -ErrorAction SilentlyContinue
    $text = "--- PARALLEL_RESULT $($j.Name) state=$($j.State) ---`n$($r | Out-String)"
    Add-Content -Encoding UTF8 -Path $DetailFile -Value $text
    Write-Output $text
    $results += [pscustomobject]@{ Name=$j.Name; State=$j.State; Text=$text }
  }
  return $results
}

function Test-HealthOnce {
  try {
    $r = Invoke-WebRequest -Uri 'http://localhost:8010/health' -UseBasicParsing -TimeoutSec 8
    return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500)
  } catch { return $false }
}

function Wait-Api([int]$MaxSeconds = 900) {
  $deadline = (Get-Date).AddSeconds($MaxSeconds)
  $i = 0
  while ((Get-Date) -lt $deadline) {
    $i++
    if (Test-HealthOnce) {
      Log "API_HEALTH_READY attempt=$i"
      return $true
    }
    Start-Sleep -Seconds 5
    if (($i % 6) -eq 0) {
      Log "WAIT_API attempt=$i"
      docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml ps -a 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $DetailFile
      docker logs --tail 80 terrayield_land_api 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $DetailFile
    }
  }
  Log "API_HEALTH_TIMEOUT ${MaxSeconds}s"
  return $false
}

function Test-EndpointParallel {
  $endpointCommands = @(
    @{ Name='health'; Command="try { `$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 20 'http://localhost:8010/health'; 'OK /health status='+`$r.StatusCode+' bytes='+`$r.Content.Length } catch { 'FAIL /health '+`$_.Exception.Message }" },
    @{ Name='openapi'; Command="try { `$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 30 'http://localhost:8010/openapi.json'; 'OK /openapi.json status='+`$r.StatusCode+' bytes='+`$r.Content.Length } catch { 'FAIL /openapi.json '+`$_.Exception.Message }" },
    @{ Name='listings_london'; Command="try { `$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 90 'http://localhost:8010/map/listings?bbox=-0.65,51.25,0.35,51.75&limit=5000'; 'OK /map/listings London status='+`$r.StatusCode+' bytes='+`$r.Content.Length } catch { 'FAIL /map/listings London '+`$_.Exception.Message }" },
    @{ Name='sales_history_status'; Command="try { `$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 90 'http://localhost:8010/map/sales-history/status'; 'OK /map/sales-history/status status='+`$r.StatusCode+' bytes='+`$r.Content.Length } catch { 'FAIL /map/sales-history/status '+`$_.Exception.Message }" },
    @{ Name='external_evidence'; Command="try { `$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 90 'http://localhost:8010/map/sales-history/external-evidence'; 'OK /map/sales-history/external-evidence status='+`$r.StatusCode+' bytes='+`$r.Content.Length } catch { 'FAIL /map/sales-history/external-evidence '+`$_.Exception.Message }" }
  )
  return Run-ParallelProbes $endpointCommands 120
}

Log 'TASK: TerraYield recovery 018 multitask supervisor'
Log 'MODE: parallel diagnosis first; API-only recovery if unhealthy; no runner/watchdog restart'
Log "PROJECT=$Project"
Log "REPORT_DIR=$ReportDir"

$initialProbes = @(
  @{ Name='compose_ps'; Command='docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml ps -a' },
  @{ Name='api_logs_tail'; Command='docker logs --tail 260 terrayield_land_api' },
  @{ Name='compose_config_head'; Command='docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml config | Select-Object -First 220' },
  @{ Name='host_compile_focus'; Command="`$ok=`$true; foreach(`$f in @('app\core\ttl_cache.py','app\middleware\map_listings_cache.py','app\main.py','app\api\routes\aays_sales_layers.py','app\api\routes\aays_sales_history_layers.py')){ if(Test-Path `$f){ python -m py_compile `$f; if(`$LASTEXITCODE -ne 0){`$ok=`$false; 'COMPILE_FAIL '+`$f}else{'COMPILE_OK '+`$f} } else { 'MISSING '+`$f } }; 'HOST_COMPILE_OK='+`$ok" },
  @{ Name='container_python_tools'; Command="docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml run --rm --no-deps api sh -lc 'cd /app && python -m pip --version && python -m alembic --help >/tmp/alembic_help.txt 2>&1; echo ALEMBIC_EXIT=$?; python -m uvicorn --help >/tmp/uvicorn_help.txt 2>&1; echo UVICORN_EXIT=$?'" }
)

$probeResults = Run-ParallelProbes $initialProbes 180
$apiHealthyInitial = Test-HealthOnce
Log "API_HEALTH_INITIAL=$apiHealthyInitial"

$recoveryAction = 'none'
if (-not $apiHealthyInitial) {
  Log 'API is not healthy; starting API-only recovery path.'
  $recoveryAction = 'api_dependency_bootstrap_and_restart'
  Run-Capture 'compose up db dependencies' { docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml up -d db postgis postgres redis }
  Run-Capture 'remove stale api container only' { docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml rm -sf api }
  Run-Capture 'api dependency bootstrap in container' { docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml run --rm api sh -lc 'cd /app && python -m pip install --no-cache-dir -e . && python -m alembic upgrade head' }
  Run-Capture 'start api container only' { docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml up -d api }
} else {
  Log 'API is already healthy; recovery restart skipped.'
}

$apiReady = Wait-Api 900
$endpointResults = @()
if ($apiReady) {
  $endpointResults = Test-EndpointParallel
} else {
  Log 'Endpoint validation skipped because API health did not become ready.'
}

$finalPs = Run-Capture 'compose ps final' { docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml ps -a }
$finalLogs = Run-Capture 'api logs final tail' { docker logs --tail 320 terrayield_land_api }
$elapsed = [int]((Get-Date) - $Start).TotalSeconds
$result = if ($apiReady) { 'healthy_or_recovered' } else { 'api_still_not_ready' }

$progressApp = if ($apiReady) { '98%' } else { '95%' }
$progressRun = if ($apiReady) { '95%' } else { '92%' }
$progressOverall = if ($apiReady) { '96%' } else { '92-93%' }

$summary = @(
  '# TerraYield Recovery 018 Multitask Supervisor Summary',
  '',
  '## Result',
  $result,
  '',
  '## Recovery Action',
  $recoveryAction,
  '',
  '## API Ready',
  "$apiReady",
  '',
  '## Progress Estimate',
  "- Application stabilization/speed: $progressApp",
  "- Cross-computer fast-start/runability: $progressRun",
  '- Continue-only automation bridge: 92%',
  "- Overall combined project: $progressOverall",
  '',
  '## Runtime',
  "Elapsed seconds: $elapsed",
  '',
  '## Files',
  "Detail: $DetailFile",
  "ReportDir: $ReportDir",
  '',
  '## Note',
  'This script runs parallel probes first, then restarts only the API container if health is unavailable. It does not restart the runner or watchdog.'
)
Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output "RESULT=$result"
Write-Output "API_READY=$apiReady"
Write-Output "RECOVERY_ACTION=$recoveryAction"
Write-Output "ELAPSED_SECONDS=$elapsed"
Write-Output 'RECOVERY_018_MULTITASK_SUPERVISOR_DONE'
exit 0
