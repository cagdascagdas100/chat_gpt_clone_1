$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\parcelsales_011_long_alt_source_scoring_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Report = Join-Path $OutDir "parcelsales_011_long_orchestrator.md"
function Add-Line($s){ Add-Content -LiteralPath $Report -Encoding UTF8 -Value $s }
Set-Content -LiteralPath $Report -Encoding UTF8 -Value "# PARCELSALES 011 Long Alternative Source + Row Scoring Orchestrator"
Add-Line "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
Add-Line "mode=read_only_no_db_write_no_production_acceptance"
Add-Line "goal=long_parallel_gap_detection_alternative_sources_row_level_scoring"
Add-Line ""
$Roots = @(
  "F:\AAYS_DATA",
  "F:\AAYS_DATA\sales_match_program",
  "F:\AAYS_DATA\terrayield_land_intelligence",
  "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
)
$SourceKeywords = @("epc","voa","ons","postcode","title","inspire","planning","uprn","address")
$ScoreColumns = @("row_confidence_score","price_score","date_score","address_score","postcode_score","property_type_score","area_score","parcel_match_score","source_score","evidence_score","conflict_score","row_reliability_band","evidence_sources_used","evidence_missing_fields","needs_review")
Add-Line "## score_columns"
foreach($c in $ScoreColumns){ Add-Line "- $c" }
Add-Line ""
for($pass=1; $pass -le 12; $pass++){
  Add-Line "## pass_$pass"
  Add-Line "pass_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
  $jobs = @()
  $jobs += Start-Job -ScriptBlock {
    param($Roots)
    $o = @()
    foreach($r in $Roots){ $o += "root=$r exists=$(Test-Path -LiteralPath $r)" }
    $o
  } -ArgumentList (,$Roots)
  $jobs += Start-Job -ScriptBlock {
    param($Roots,$Keywords)
    $hits = @()
    foreach($r in $Roots){
      if(Test-Path -LiteralPath $r){
        $files = Get-ChildItem -LiteralPath $r -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 2000
        foreach($f in $files){
          foreach($k in $Keywords){ if($f.Name.ToLower().Contains($k)){ $hits += "$k|$($f.FullName)"; break } }
          if($hits.Count -ge 80){ break }
        }
      }
      if($hits.Count -ge 80){ break }
    }
    if($hits.Count -eq 0){ "no_alt_source_candidates_found" } else { $hits | Select-Object -First 80 }
  } -ArgumentList (,$Roots),(,$SourceKeywords)
  $jobs += Start-Job -ScriptBlock {
    param($BridgeRoot)
    $dirs = @("ai-results","ai-heartbeat","ai-runner-outputs")
    $o = @()
    foreach($d in $dirs){
      $p = Join-Path $BridgeRoot $d
      $count = 0
      if(Test-Path -LiteralPath $p){ $count = @(Get-ChildItem -LiteralPath $p -File -Recurse -ErrorAction SilentlyContinue).Count }
      $o += "$d files=$count"
    }
    $o
  } -ArgumentList $BridgeRoot
  $allDone = Wait-Job -Job $jobs -Timeout 120
  foreach($j in $jobs){
    if($j.State -eq "Running"){
      Stop-Job -Job $j -Force
      Add-Line "job_timeout_detected_and_stopped id=$($j.Id)"
    } else {
      $data = Receive-Job -Job $j -ErrorAction SilentlyContinue
      foreach($line in $data){ Add-Line "$line" }
    }
    Remove-Job -Job $j -Force -ErrorAction SilentlyContinue
  }
  Add-Line "pass_$pass done"
  Add-Line ""
  if($pass -lt 12){ Start-Sleep -Seconds 170 }
}
Add-Line "## final_decision"
Add-Line "- Previous sales outputs remain baseline only."
Add-Line "- Alternative evidence sources must improve each row independently."
Add-Line "- Rows without source/evidence must be downgraded or unmatched."
Add-Line "- Next implementation should sample 50 rows and emit row-level scores before full run."
Add-Line "end_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
Write-Host "PARCELSALES_011_OUTPUT=$OutDir"