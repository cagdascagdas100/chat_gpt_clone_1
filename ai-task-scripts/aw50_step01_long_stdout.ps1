$ErrorActionPreference = "Stop"
$pkg = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\docs\chatgpt_handoff\accuracy_warehouse_50step"
Write-Host "# AW50 Step 1 Long Stdout Orchestrator"
Write-Host "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
Write-Host "scope=step1_only_stdout_no_file_lock_no_db_write"
Write-Host "package_root=$pkg"
if (!(Test-Path $pkg -PathType Container)) { Write-Host "STEP_1_FAIL"; Write-Host "reason=PACKAGE_ROOT_MISSING"; exit 10 }
$failed = 0
for($pass=1; $pass -le 8; $pass++){
  Write-Host "pass=$pass"
  Write-Host "pass_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
  $items = Get-ChildItem -LiteralPath $pkg -File -Filter "AW50_*" | Sort-Object Name
  Write-Host "aw50_file_count=$($items.Count)"
  foreach($it in $items){
    $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $it.FullName).Hash.ToLower()
    Write-Host "file=$($it.Name) sha256=$h verdict=present"
  }
  if($items.Count -lt 20){ $failed++ ; Write-Host "pass_verdict=fail" } else { Write-Host "pass_verdict=pass" }
  if($pass -lt 8){ Start-Sleep -Seconds 240 }
}
Write-Host "secret_values_printed=false"
Write-Host "db_write=none"
Write-Host "ddl=none"
Write-Host "migration_apply=none"
Write-Host "prod_deploy=none"
if($failed -eq 0){ Write-Host "STEP_1_PASS"; Write-Host "aw50_progress=1/50"; Write-Host "aw50_progress_percent=2"; exit 0 }
Write-Host "STEP_1_FAIL"
exit 1
