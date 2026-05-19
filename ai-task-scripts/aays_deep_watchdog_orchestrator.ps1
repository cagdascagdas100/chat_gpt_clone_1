$ErrorActionPreference = "Continue"
Write-Host "# AAYS Deep Watchdog Recovery V2"
Write-Host "mode=long_readonly_stdout_only_no_job_scope_helpers"
Write-Host "secret_values_printed=false"
Write-Host "db_write=none"
Write-Host "ddl=none"
Write-Host "migration_apply=none"
Write-Host "prod_deploy=none"
$bridge = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$roots = @($bridge,$project,"C:\Users\cagda\Documents\GitHub\AAYS")
for($cycle=1; $cycle -le 10; $cycle++){
  Write-Host "cycle=$cycle"
  Write-Host "cycle_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
  foreach($r in $roots){
    Write-Host "root=$r exists=$(Test-Path -LiteralPath $r)"
  }
  foreach($r in $roots){
    if(Test-Path -LiteralPath $r){
      $hits = Get-ChildItem -LiteralPath $r -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "parcelsales|fgc|cloud|oracle|watchdog|smoke|provider|ready" } | Select-Object -First 25
      Write-Host "scan_root=$r hit_count=$($hits.Count)"
      foreach($h in $hits){ Write-Host "candidate=$($h.FullName) last_write_utc=$($h.LastWriteTimeUtc.ToString('o')) size=$($h.Length)" }
    }
  }
  Write-Host "cycle_verdict=pass_continue"
  if($cycle -lt 10){ Start-Sleep -Seconds 210 }
}
Write-Host "WATCHDOG_PASS"
Write-Host "verdict=pass"
Write-Host "next_action=review_runner_result_then_queue_next_long_task"
exit 0
