$ErrorActionPreference = "Continue"
$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$BranchExpected = "security-accuracy-expansion-20260508"
$OutDir = Join-Path $Repo "docs\chatgpt_handoff\cloud_ready_20260517"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Report = Join-Path $OutDir "012B_LOCAL_TEST_SMOKE_PERF_REPORT.txt"
$Blockers = Join-Path $OutDir "012B_LOCAL_TEST_SMOKE_PERF_BLOCKERS.md"
$PytestOut = Join-Path $OutDir "012B_TARGETED_PYTEST_OUTPUT.txt"
$SmokeOut = Join-Path $OutDir "012B_LOCAL_API_SMOKE.jsonl"
$PerfOut = Join-Path $OutDir "012B_PERF_SUMMARY.txt"
$PublishLog = Join-Path $OutDir "012B_PUBLISH_LOG.txt"
$B = New-Object System.Collections.Generic.List[string]
function AB($x){ if(-not $B.Contains($x)){ $B.Add($x) } }
function P95($url,$warm,$n){ for($i=0;$i -lt $warm;$i++){try{curl.exe -sS -L --compressed --max-time 8 -o NUL $url|Out-Null}catch{}}; $vals=@(); for($i=0;$i -lt $n;$i++){try{$raw=curl.exe -sS -L --compressed --max-time 8 -o NUL -w "%{time_total}" $url; $v=0.0; if([double]::TryParse($raw,[Globalization.NumberStyles]::Float,[Globalization.CultureInfo]::InvariantCulture,[ref]$v)){$vals += [math]::Round($v*1000,2)}}catch{}}; if($vals.Count -eq 0){return $null}; $s=$vals|Sort-Object; $idx=[math]::Ceiling(0.95*$s.Count)-1; if($idx -lt 0){$idx=0}; if($idx -ge $s.Count){$idx=$s.Count-1}; return [double]$s[$idx] }
Set-Location $Repo
$Before=(git branch --show-current).Trim()
git fetch origin $BranchExpected | Out-Null
git checkout $BranchExpected | Out-Null
git pull --ff-only origin $BranchExpected | Out-Null
$Branch=(git branch --show-current).Trim(); $Head=(git rev-parse --short=12 HEAD).Trim()
if($Branch -ne $BranchExpected){AB "BRANCH_MISMATCH"}
$Tests=@("tests\test_source_confidence_rules.py","tests\test_source_confidence_integration.py","tests\test_scoring.py","tests\test_source_manifest_status.py","tests\test_sale_land_verification_route.py","tests\test_parcel_matcher_source_confidence.py")
$Existing=@(); foreach($t in $Tests){ if(Test-Path (Join-Path $Repo $t)){$Existing += $t} }
$PytestStatus="failed"; $PyExit="not_run"
if($Existing.Count -gt 0){ $po=python -m pytest @Existing -q 2>&1; $PyExit=$LASTEXITCODE; @("pytest_exit_code=$PyExit","existing_tests=$($Existing -join ';')","",$po)|Set-Content -LiteralPath $PytestOut -Encoding UTF8; if($PyExit -eq 0){$PytestStatus="passed"}else{AB "TARGETED_PYTEST_FAILED"} } else { AB "NO_TARGETED_TESTS_FOUND" }
$Base="http://127.0.0.1:8010"; $Eps=@("/","/ops/storage-registry","/ops/consistency-check","/handoff/status","/map/listings?limit=1","/map/sales-history/combined?limit=1")
Remove-Item $SmokeOut -Force -ErrorAction SilentlyContinue
$Ok=0
foreach($ep in $Eps){$status="error";$code="";$ms="";try{$sw=[Diagnostics.Stopwatch]::StartNew();$r=Invoke-WebRequest -UseBasicParsing -Uri ($Base+$ep) -TimeoutSec 10;$sw.Stop();$code=[string]$r.StatusCode;$ms=[string][Math]::Round($sw.Elapsed.TotalMilliseconds,2);if($r.StatusCode -ge 200 -and $r.StatusCode -lt 500){$status="ok";$Ok++}}catch{$code="exception";$ms="connection_or_timeout"}; @{endpoint=$ep;status=$status;status_code=$code;elapsed_ms=$ms}|ConvertTo-Json -Compress|Add-Content -LiteralPath $SmokeOut -Encoding UTF8}
$ApiStatus=if($Ok -eq $Eps.Count){"local_passed"}else{"blocked"; AB "LOCAL_API_SMOKE_FAILED"}
$Warm=15;$Samples=30;$P1=P95 ($Base+"/handoff/status") $Warm $Samples;$P2=P95 ($Base+"/map/listings?limit=200") $Warm $Samples;$P3=P95 ($Base+"/map/sales-history/combined?limit=200") $Warm $Samples
$PerfStatus="passed"; if($null -eq $P1 -or $P1 -ge 600){$PerfStatus="failed"}; if($null -eq $P2 -or $P2 -ge 1500){$PerfStatus="failed"}; if($null -eq $P3 -or $P3 -ge 1800){$PerfStatus="failed"}; if($PerfStatus -ne "passed"){AB "PERFORMANCE_GATE_FAILED"}
@("measurement_client=curl.exe -o NUL -w time_total","warmup_count=$Warm","sample_count=$Samples","p95_from_time_total_only=true","handoff_status_p95_ms=$P1","map_listings_limit_200_p95_ms=$P2","map_sales_history_combined_limit_200_p95_ms=$P3","performance_gate_status=$PerfStatus") | Set-Content -LiteralPath $PerfOut -Encoding UTF8
$Final=if($B.Count -eq 0){"CLOUD_READY_PENDING_PROVIDER"}else{"BLOCKED"}; $Next=if($B.Count -eq 0){"WAIT_FOR_USER_PROVIDER_DECISION"}else{$B[0]}
@("timestamp_utc=$([DateTime]::UtcNow.ToString('o'))","task=012B_LOCAL_TEST_SMOKE_PERF_AND_PUBLISH","repo=$Repo","branch_before=$Before","checked_branch=$Branch","head=$Head","pytest_status=$PytestStatus","pytest_exit_code=$PyExit","api_smoke_status=$ApiStatus","api_smoke_ok_count=$Ok","api_smoke_total=$($Eps.Count)","perf_status=$PerfStatus","perf_p95_ms__handoff_status=$P1","perf_p95_ms__map_listings_limit_200=$P2","perf_p95_ms__map_sales_history_combined_limit_200=$P3","public_url_verified=false","cloud_db_verified=false","final_classification=$Final","next_single_action=$Next","secret_values_printed=false","db_write=none","ddl=none","migration_apply=none","prod_deploy=none","blockers=$(if($B.Count -eq 0){'none'}else{($B -join ';')})") | Set-Content -LiteralPath $Report -Encoding UTF8
$BL=@("# 012B Blockers",""); if($B.Count -eq 0){$BL += "- none"}else{foreach($x in $B){$BL += "- $x"}}; $BL|Set-Content -LiteralPath $Blockers -Encoding UTF8
git add "docs/chatgpt_handoff/cloud_ready_20260517" 2>&1 | Tee-Object -FilePath $PublishLog
if(git diff --cached --name-only){ git commit -m "Publish 012B local test smoke perf evidence" 2>&1 | Tee-Object -FilePath $PublishLog -Append; if($LASTEXITCODE -eq 0){ git push origin $BranchExpected 2>&1 | Tee-Object -FilePath $PublishLog -Append } }
Get-Content $Report
Get-Content $Blockers
