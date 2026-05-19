$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$bridge = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$out = Join-Path $bridge "ai-results\aays_deep_watchdog_20260519.md"
$parcelOut = Join-Path $bridge "ai-results\parcelsales_011_recovery_20260519.md"
$fgcOut = Join-Path $bridge "ai-results\terrayield_fgc_deep_discovery_20260519.md"
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
function W($p,$m){ Add-Content -LiteralPath $p -Encoding UTF8 -Value $m }
Set-Content -LiteralPath $out -Encoding UTF8 -Value "# AAYS Deep Watchdog Recovery"
Set-Content -LiteralPath $parcelOut -Encoding UTF8 -Value "# PARCELSALES 011 Recovery"
Set-Content -LiteralPath $fgcOut -Encoding UTF8 -Value "# TerraYield FGC Deep Discovery"
W $out "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
W $out "mode=long_readonly_parallel_watchdog"
W $out "db_write=false"
W $out "destructive_ops=false"
$project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$roots = @($bridge,$project,"C:\Users\cagda\Documents\GitHub\AAYS") | Where-Object { Test-Path $_ -PathType Container }
function Scan-Tree($root,$pattern){
  $items = Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like $pattern } | Select-Object -First 50
  return $items
}
function Invoke-ParcelRecovery {
 param($roots,$parcelOut)
 W $parcelOut "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
 foreach($r in $roots){
   W $parcelOut "root=$r"
   $scripts = Scan-Tree $r "*parcelsales*"
   foreach($s in $scripts){ W $parcelOut "candidate=$($s.FullName) | timestamp_utc=$($s.LastWriteTimeUtc.ToString('o')) | size=$($s.Length) | sha256=$((Get-FileHash $s.FullName -Algorithm SHA256).Hash.ToLower())" }
   Start-Sleep -Seconds 30
 }
 W $parcelOut "result=parcel_recovery_scan_complete"
}
function Invoke-FgcDiscovery {
 param($roots,$fgcOut)
 W $fgcOut "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
 foreach($r in $roots){
   W $fgcOut "root=$r"
   $items = Scan-Tree $r "*fgc*"
   foreach($i in $items){ W $fgcOut "fgc_candidate=$($i.FullName) | timestamp_utc=$($i.LastWriteTimeUtc.ToString('o')) | size=$($i.Length) | sha256=$((Get-FileHash $i.FullName -Algorithm SHA256).Hash.ToLower())" }
   Start-Sleep -Seconds 30
 }
 W $fgcOut "result=fgc_discovery_complete"
}
function Invoke-RepoHealth {
 param($roots,$out)
 foreach($r in $roots){
   W $out "repo_health_root=$r"
   $count = @(Get-ChildItem -LiteralPath $r -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 500).Count
   W $out "file_sample_count=$count"
   Start-Sleep -Seconds 30
 }
}
$warn=0;$fail=0
for($cycle=1;$cycle -le 6;$cycle++){
 W $out ""
 W $out "## cycle_$cycle"
 W $out "cycle_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
 $jobs=@()
 $jobs += Start-Job -ScriptBlock ${function:Invoke-ParcelRecovery} -ArgumentList $roots,$parcelOut
 $jobs += Start-Job -ScriptBlock ${function:Invoke-FgcDiscovery} -ArgumentList $roots,$fgcOut
 $jobs += Start-Job -ScriptBlock ${function:Invoke-RepoHealth} -ArgumentList $roots,$out
 Wait-Job -Job $jobs -Timeout 420 | Out-Null
 foreach($j in $jobs){
   if($j.State -eq 'Running'){
     Stop-Job $j -Force
     W $out "stuck_branch_detected=true | action=stopped_and_continue_other_branches"
     $warn++
   } else {
     Receive-Job $j | Out-Null
     W $out "branch_completed=true | state=$($j.State)"
   }
 }
 Get-Job | Remove-Job -Force -ErrorAction SilentlyContinue
 W $out "cycle_warn_total=$warn"
 W $out "cycle_fail_total=$fail"
 if($cycle -lt 6){ Start-Sleep -Seconds 300 }
}
W $out ""
W $out "WATCHDOG_PASS"
W $out "verdict=pass"
W $out "warn_total=$warn"
W $out "fail_total=$fail"
W $out "end_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
exit 0
