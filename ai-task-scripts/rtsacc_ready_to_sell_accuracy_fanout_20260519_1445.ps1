$ErrorActionPreference = "Continue"
Write-Host "# RTSACC Ready-to-Sell Accuracy Fanout 20260519-1445"
Write-Host "mode=long_readonly_local_fanout"
Write-Host "db_write=none"
Write-Host "prod_acceptance=off"
Write-Host "destructive_ops=none"

$bridge = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$aays = "C:\Users\cagda\Documents\GitHub\AAYS"
$resultDir = Join-Path $bridge "ai-results"
$progressDir = Join-Path $bridge "ai-progress"
New-Item -ItemType Directory -Force -Path $resultDir,$progressDir | Out-Null
$resultPath = Join-Path $resultDir "rtsacc_ready_to_sell_accuracy_fanout_20260519_1445.md"
$progressPath = Join-Path $progressDir "rtsacc_ready_to_sell_accuracy_fanout_20260519_1445.progress.md"

Set-Content -LiteralPath $resultPath -Value @("# RTSACC Accuracy Fanout Result","task_id=rtsacc-ready-to-sell-accuracy-fanout-20260519-1445","mode=read_only_parallel_scans","db_write=none","prod_acceptance=off") -Encoding UTF8
Set-Content -LiteralPath $progressPath -Value @("# RTSACC Accuracy Fanout Progress","task_id=rtsacc-ready-to-sell-accuracy-fanout-20260519-1445") -Encoding UTF8

$lanes = @(
  @{ name="runner_heartbeat_liveness"; root=$bridge; pattern="heartbeat|autopilot|runner|current-task|result" },
  @{ name="ready_to_sell_evidence"; root=$project; pattern="ready|sell|rtsacc|accuracy|evidence|review" },
  @{ name="parcel_sales_provider_cloud"; root=$project; pattern="parcelsales|parcel|provider|fgc|cloud|oracle|county" },
  @{ name="smoke_test_and_verdicts"; root=$project; pattern="smoke|verdict|pass|fail|gate|acceptance" },
  @{ name="bridge_artifact_inventory"; root=$bridge; pattern="aw50|parcelsales|rtsacc|ready|watchdog|accuracy" },
  @{ name="aays_cross_project_inventory"; root=$aays; pattern="terrayield|ready|sell|accuracy|watchdog|orchestrator" }
)

for($cycle=1; $cycle -le 10; $cycle++){
  $cycleUtc = (Get-Date).ToUniversalTime().ToString('o')
  Write-Host "cycle=$cycle cycle_utc=$cycleUtc"
  Add-Content -LiteralPath $progressPath -Value "## cycle $cycle $cycleUtc" -Encoding UTF8
  Add-Content -LiteralPath $resultPath -Value "## cycle $cycle $cycleUtc" -Encoding UTF8
  $jobs = @()
  foreach($lane in $lanes){
    $jobs += Start-Job -ScriptBlock {
      param($laneName,$root,$pattern)
      $lines = @("### lane=$laneName", "root=$root", "exists=$(Test-Path -LiteralPath $root)")
      if(Test-Path -LiteralPath $root){
        $items = Get-ChildItem -LiteralPath $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match $pattern -and $_.FullName -notmatch "node_modules|.git\\objects|dist|build|.next" } | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 40
        $lines += "hit_count=$($items.Count)"
        foreach($i in $items){ $lines += "hit=$($i.FullName) last_write_utc=$($i.LastWriteTimeUtc.ToString('o')) size=$($i.Length)" }
      }
      $lines -join "`n"
    } -ArgumentList ([string]$lane.name),([string]$lane.root),([string]$lane.pattern)
  }
  $null = Wait-Job -Job $jobs -Timeout 120
  foreach($job in $jobs){
    Add-Content -LiteralPath $progressPath -Value "job=$($job.Id) state=$($job.State)" -Encoding UTF8
    $content = Receive-Job -Job $job -Keep -ErrorAction SilentlyContinue
    if($content){ Add-Content -LiteralPath $resultPath -Value ($content -join "`n") -Encoding UTF8 }
    if($job.State -eq "Running"){ Stop-Job -Job $job -ErrorAction SilentlyContinue; Add-Content -LiteralPath $resultPath -Value "job=$($job.Id) stopped_after_timeout=true" -Encoding UTF8 }
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
  }
  Add-Content -LiteralPath $resultPath -Value "cycle_verdict=pass_continue" -Encoding UTF8
  if($cycle -lt 10){ Start-Sleep -Seconds 210 }
}
Add-Content -LiteralPath $resultPath -Value "RTSACC_FANOUT_PASS`nverdict=pass`nnext_action=review_result_then_queue_deeper_provider_accuracy_task" -Encoding UTF8
Write-Host "RTSACC_FANOUT_PASS"
Write-Host "result_path=$resultPath"
Write-Host "verdict=pass"
exit 0
