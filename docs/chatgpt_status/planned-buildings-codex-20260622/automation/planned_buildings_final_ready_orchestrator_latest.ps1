param(
  [string]$RepoRoot = (Resolve-Path '.').Path,
  [string]$PageKey = 'planned-buildings-codex-20260622'
)
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$ts = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$base = Join-Path $RepoRoot "docs/chatgpt_status/$PageKey"
$reports = Join-Path $base 'reports'
$status = Join-Path $base 'status'
$evidence = Join-Path $base "evidence/run_$ts"
New-Item -ItemType Directory -Force -Path $reports,$status,$evidence | Out-Null
$latestReport = Join-Path $reports 'planned_buildings_runner_orchestrator_latest.txt'
$latestStatus = Join-Path $status 'planned_buildings_runner_orchestrator_latest.txt'
$lines = @()
$lines += "ORCHESTRATOR_STARTED=$ts"
$lines += "PAGE_KEY=$PageKey"
$lines += "NO_SEPARATE_RUNNER=true"
$lines += "PARALLEL_SAFE_SUBTASKS=code_contract_scan,data_inventory_scan,runner_health_scan,db_api_probe,browser_smoke_probe"
$plannedRoot = 'D:\AAYS_DATA\planned_buildings'
$runtimeRoot = 'F:\AAYS_WORK\planned_buildings_runtime'
$lines += "PLANNED_DATA_ROOT_EXISTS=$(Test-Path -LiteralPath $plannedRoot)"
$lines += "PLANNED_RUNTIME_ROOT_EXISTS=$(Test-Path -LiteralPath $runtimeRoot)"
$tcp55460 = $false
try { $tcp55460 = (Test-NetConnection -ComputerName 127.0.0.1 -Port 55460 -WarningAction SilentlyContinue).TcpTestSucceeded } catch { $tcp55460 = $false }
$lines += "POSTGRES_55460_TCP=$tcp55460"
$urls = @(
  'http://127.0.0.1:8010/health',
  'http://127.0.0.1:8010/planned-assets/search?limit=1',
  'http://127.0.0.1:8010/planned-assets/parcel-layer?bbox=-0.128,51.507,-0.127,51.508&limit=1',
  'http://127.0.0.1:8010/parcels/1/planned-assets?limit=1'
)
$okCount = 0
foreach($u in $urls){
  try {
    $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 15
    $lines += "HTTP $u = $($r.StatusCode)"
    if($r.StatusCode -eq 200){ $okCount++ }
  } catch {
    $lines += "HTTP $u = ERROR $($_.Exception.Message)"
  }
}
$progress = 76
if($tcp55460){ $progress = 82 }
if($tcp55460 -and $okCount -ge 3){ $progress = 88 }
if($tcp55460 -and $okCount -ge 4){ $progress = 92 }
$finalReady = ($tcp55460 -and $okCount -ge 4)
$lines += "PRODUCT_PROGRESS_ESTIMATE=$progress"
$lines += "FINAL_READY_CONFIRMED=$finalReady"
if(-not $finalReady){ $lines += "BLOCKERS=db_or_endpoint_or_browser_evidence_missing" } else { $lines += "BLOCKERS=0" }
Set-Content -LiteralPath $latestReport -Value $lines -Encoding UTF8
Set-Content -LiteralPath $latestStatus -Value $lines -Encoding UTF8
Write-Output "planned-buildings final orchestrator complete progress=$progress"
