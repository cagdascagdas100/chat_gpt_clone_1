$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\parcelsales_012_long_sample_scoring_prep_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Report = Join-Path $OutDir "parcelsales_012_long_sample_scoring_prep.md"
Set-Content -LiteralPath $Report -Encoding UTF8 -Value "# PARCELSALES 012 Long Sample Scoring Prep"
Add-Content -LiteralPath $Report -Encoding UTF8 -Value "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
Add-Content -LiteralPath $Report -Encoding UTF8 -Value "mode=read_only_long_sample_scoring_prep"
$Bridge = $BridgeRoot
$SalesMaster = "F:\AAYS_DATA\sales_match_program\master\master_sales_rows.csv"
$SalesXlsx = "F:\AAYS_DATA\sales_match_program\master\historical_sales_parcel_matched_england_wales.xlsx"
$Roots = @("F:\AAYS_DATA", "F:\AAYS_DATA\terrayield_land_intelligence", "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence")
$Keywords = @("epc","voa","ons","postcode","title","inspire","planning","uprn","address")
for($pass=1; $pass -le 10; $pass++){
  Add-Content -LiteralPath $Report -Encoding UTF8 -Value ""
  Add-Content -LiteralPath $Report -Encoding UTF8 -Value "## pass_$pass $((Get-Date).ToUniversalTime().ToString('o'))"
  $jobs = @()
  $jobs += Start-Job -ScriptBlock {
    param($SalesMaster,$SalesXlsx)
    $o=@()
    $o += "master_csv_exists=$(Test-Path -LiteralPath $SalesMaster)"
    $o += "master_xlsx_exists=$(Test-Path -LiteralPath $SalesXlsx)"
    if(Test-Path -LiteralPath $SalesMaster){
      $rows = Import-Csv -LiteralPath $SalesMaster | Select-Object -First 50
      $o += "sample_rows=$(@($rows).Count)"
      if(@($rows).Count -gt 0){ $o += "sample_columns=$($rows[0].PSObject.Properties.Name -join ',')" }
    }
    $o
  } -ArgumentList $SalesMaster,$SalesXlsx
  $jobs += Start-Job -ScriptBlock {
    param($Roots,$Keywords)
    $o=@(); $count=0
    foreach($r in $Roots){
      $o += "root=$r exists=$(Test-Path -LiteralPath $r)"
      if(Test-Path -LiteralPath $r){
        $files = Get-ChildItem -LiteralPath $r -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1500
        foreach($f in $files){
          foreach($k in $Keywords){
            if($f.Name.ToLower().Contains($k)){ $o += "candidate=$k|$($f.FullName)"; $count++; break }
          }
          if($count -ge 40){ break }
        }
      }
      if($count -ge 40){ break }
    }
    $o += "candidate_count_listed=$count"
    $o
  } -ArgumentList (,$Roots),(,$Keywords)
  $jobs += Start-Job -ScriptBlock {
    param($Bridge)
    $o=@()
    foreach($d in @("ai-results","ai-heartbeat","ai-runner-outputs","ai-task-scripts")){
      $p=Join-Path $Bridge $d
      $c=0
      if(Test-Path -LiteralPath $p){ $c=@(Get-ChildItem -LiteralPath $p -Recurse -File -ErrorAction SilentlyContinue).Count }
      $o += "$d file_count=$c"
    }
    $o
  } -ArgumentList $Bridge
  Wait-Job -Job $jobs -Timeout 120 | Out-Null
  foreach($j in $jobs){
    if($j.State -eq "Running"){
      Stop-Job -Job $j -Force
      Add-Content -LiteralPath $Report -Encoding UTF8 -Value "job_timeout_stopped=$($j.Id)"
    } else {
      $data = Receive-Job -Job $j -ErrorAction SilentlyContinue
      foreach($line in $data){ Add-Content -LiteralPath $Report -Encoding UTF8 -Value $line }
    }
    Remove-Job -Job $j -Force -ErrorAction SilentlyContinue
  }
  Add-Content -LiteralPath $Report -Encoding UTF8 -Value "pass_$pass complete"
  if($pass -lt 10){ Start-Sleep -Seconds 180 }
}
Add-Content -LiteralPath $Report -Encoding UTF8 -Value ""
Add-Content -LiteralPath $Report -Encoding UTF8 -Value "## next"
Add-Content -LiteralPath $Report -Encoding UTF8 -Value "Prepare 50-row scoring sample only after reviewing candidate alternative sources."
Add-Content -LiteralPath $Report -Encoding UTF8 -Value "end_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
Write-Host "PARCELSALES_012_OUTPUT=$OutDir"