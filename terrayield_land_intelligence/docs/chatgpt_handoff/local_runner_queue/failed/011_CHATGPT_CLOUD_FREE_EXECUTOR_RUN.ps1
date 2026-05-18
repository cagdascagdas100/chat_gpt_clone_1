$ErrorActionPreference = "Continue"
$TaskName = "011_CHATGPT_CLOUD_FREE_EXECUTOR_RUN"
$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
$MainRepo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$ExpectedBranch = "security-accuracy-expansion-20260508"
$OutDir = Join-Path $Repo "docs\chatgpt_handoff\cloud_ready_20260517"
$MainOut = Join-Path $MainRepo "docs\chatgpt_handoff\cloud_ready_20260517"
New-Item -ItemType Directory -Force -Path $OutDir,$MainOut | Out-Null
$Report = Join-Path $OutDir "EXECUTION_REPORT.txt"
$Blockers = Join-Path $OutDir "BLOCKERS.md"
$Location = Join-Path $OutDir "LOCATION_EVIDENCE_SAMPLE.jsonl"
$Perf = Join-Path $OutDir "PERF_SUMMARY.txt"
$Safety = Join-Path $OutDir "SAFETY_SUMMARY.txt"
$PublishLog = Join-Path $OutDir "011_PUBLISH_LOG.txt"
$B = New-Object System.Collections.Generic.List[string]
function AB($x){ if(-not $B.Contains($x)){ $B.Add($x) } }
function P95($url,$warm,$n){
  for($i=0;$i -lt $warm;$i++){ try{ curl.exe -sS -L --compressed --max-time 5 -o NUL $url | Out-Null }catch{} }
  $vals=@()
  for($i=0;$i -lt $n;$i++){ try{ $raw=curl.exe -sS -L --compressed --max-time 5 -o NUL -w "%{time_total}" $url; $v=0.0; if([double]::TryParse($raw,[Globalization.NumberStyles]::Float,[Globalization.CultureInfo]::InvariantCulture,[ref]$v)){ $vals += [Math]::Round($v*1000,2) } }catch{} }
  if($vals.Count -eq 0){ return $null }
  $s=$vals|Sort-Object; $idx=[Math]::Ceiling(0.95*$s.Count)-1; if($idx -lt 0){$idx=0}; if($idx -ge $s.Count){$idx=$s.Count-1}; return [double]$s[$idx]
}
Set-Location $Repo
$Branch = (git branch --show-current).Trim()
$HeadBefore = (git rev-parse --short=8 HEAD).Trim()
git fetch origin $ExpectedBranch | Out-Null
git pull origin $ExpectedBranch | Out-Null
$HeadAfter = (git rev-parse --short=8 HEAD).Trim()
if($Branch -ne $ExpectedBranch){ AB "BLOCKED_BY_BRANCH_MISMATCH" }
$Required=@("Dockerfile.cloud","render.example.yaml",".env.cloud.example","scripts\cloud_smoke_check.py","docs\cloud_ready\STATUS.md")
$Missing=@()
foreach($f in $Required){ if(-not (Test-Path (Join-Path $Repo $f))){ $Missing += $f } }
if($Missing.Count -gt 0){ AB ("BLOCKED_BY_MISSING_CLOUD_FILES:" + ($Missing -join ",")) }
$PyOut = pytest .\tests\test_source_confidence_rules.py .\tests\test_source_confidence_integration.py .\tests\test_scoring.py .\tests\test_source_manifest_status.py .\tests\test_sale_land_verification_route.py .\tests\test_parcel_matcher_source_confidence.py -q 2>&1
$PyExit=$LASTEXITCODE
if($PyExit -ne 0){ AB "BLOCKED_BY_TARGETED_TESTS" }
$Base="http://127.0.0.1:8010"
$Eps=@("/","/ops/storage-registry","/ops/consistency-check","/handoff/status","/map/listings?limit=1","/map/sales-history/combined?limit=1")
$Ok=0
foreach($ep in $Eps){ try{ $r=Invoke-WebRequest -UseBasicParsing -Uri ($Base+$ep) -TimeoutSec 8; if($r.StatusCode -ge 200 -and $r.StatusCode -lt 500){$Ok++} }catch{} }
if($Ok -ne $Eps.Count){ AB "BLOCKED_BY_LOCAL_API_SMOKE" }
$DockerStatus="failed"
try{ docker exec terrayield_land_postgis psql -U postgres -d terrayield_land -c "SHOW transaction_read_only; SELECT current_database();" 1>$null 2>$null; if($LASTEXITCODE -eq 0){$DockerStatus="passed"} }catch{}
if($DockerStatus -ne "passed"){ AB "BLOCKED_BY_DOCKER_POSTGIS_READONLY" }
$Warm=15; $Samples=30
$P1=P95 ($Base+"/handoff/status") $Warm $Samples
$P2=P95 ($Base+"/map/listings?limit=200") $Warm $Samples
$P3=P95 ($Base+"/map/sales-history/combined?limit=200") $Warm $Samples
$PerfStatus="passed"
if($null -eq $P1 -or $P1 -ge 600){$PerfStatus="failed"}
if($null -eq $P2 -or $P2 -ge 1500){$PerfStatus="failed"}
if($null -eq $P3 -or $P3 -ge 1800){$PerfStatus="failed"}
if($PerfStatus -ne "passed"){ AB "BLOCKED_BY_PERFORMANCE_GATE" }
$CloudSmoke="blocked"
$Public=$env:TERRAYIELD_PUBLIC_API_URL
if($Public){ try{ $CloudOut=python .\scripts\cloud_smoke_check.py 2>&1; if(($CloudOut -join "`n") -match "CLOUD_RUNTIME_READY"){$CloudSmoke="passed"}else{$CloudSmoke="blocked"} }catch{} }
$Final="CLOUD_READY_PENDING_PROVIDER"
$Next="ADD_PROVIDER_PUBLIC_URL_AND_CLOUD_DB_SETTINGS_OUTSIDE_REPO"
if($CloudSmoke -eq "passed" -and $B.Count -eq 0){ $Final="FREE_TIER_BEST_EFFORT_READY"; $Next="done" }
$Comp=75
if($B.Count -eq 0 -and $CloudSmoke -eq "blocked"){$Comp=85}
if($Final -eq "FREE_TIER_BEST_EFFORT_READY"){$Comp=100}
$Remain=100-$Comp
$BlockText=if($B.Count -eq 0){"none"}else{($B -join ";")}
@(
"timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
"task=$TaskName",
"branch_current=$Branch",
"head_before=$HeadBefore",
"head_after=$HeadAfter",
"cloud_files_missing=$($Missing -join ';')",
"pytest_status=$(if($PyExit -eq 0){'passed'}else{'failed'})",
"api_smoke_status=$(if($Ok -eq $Eps.Count){'local_passed'}else{'blocked'})",
"cloud_smoke_status=$CloudSmoke",
"perf_status=$PerfStatus",
"api_smoke_ok_count=$Ok",
"api_smoke_total=$($Eps.Count)",
"docker_readonly_probe_status=$DockerStatus",
"perf_measurement_client=curl.exe -o NUL -w time_total",
"perf_p95_ms__handoff_status=$P1",
"perf_p95_ms__map_listings_limit_200=$P2",
"perf_p95_ms__map_sales_history_combined_limit_200=$P3",
"performance_gate_status=$PerfStatus",
"completion_percent=$Comp",
"remaining_percent=$Remain",
"overall_execution_completion_percent=$Comp",
"remaining_work_percent=$Remain",
"final_classification=$Final",
"next_single_action=$Next",
"secret_values_printed=false",
"db_write=none",
"ddl=none",
"migration_apply=none",
"prod_deploy=none",
"report_dir=$OutDir",
"blockers=$BlockText"
) | Set-Content -LiteralPath $Report -Encoding UTF8
$BL=@("# Blockers","")
if($B.Count -eq 0){$BL += "- none"}else{foreach($x in $B){$BL += "- $x"}}
if($CloudSmoke -eq "blocked"){$BL += "- provider_public_url_not_verified"}
$BL | Set-Content -LiteralPath $Blockers -Encoding UTF8
@{parcel_id="sample-not-probed";source_system="not_probed";source_url=$null;source_file="not_probed";srid="unknown";coordinate_order="unknown";geometry_type="unknown";centroid_lat=$null;centroid_lon=$null;bbox=$null;match_method="not_probed";match_confidence=0;confidence_reason="template_only";evidence_count=0;last_verified_utc=[DateTime]::UtcNow.ToString('o');cannot_be_high_confidence_if_source_url_missing=$true;high_confidence=$false} | ConvertTo-Json -Compress | Set-Content -LiteralPath $Location -Encoding UTF8
@("measurement_client=curl.exe -o NUL -w time_total","warmup_count=$Warm","sample_count=$Samples","p95_from_time_total_only=true","handoff_status_p95_ms=$P1","map_listings_limit_200_p95_ms=$P2","map_sales_history_combined_limit_200_p95_ms=$P3","performance_gate_status=$PerfStatus") | Set-Content -LiteralPath $Perf -Encoding UTF8
@("db_write=none","ddl=none","migration_apply=none","prod_deploy=none","secret_values_printed=false") | Set-Content -LiteralPath $Safety -Encoding UTF8
Copy-Item $Report (Join-Path $MainOut "EXECUTION_REPORT.txt") -Force
Copy-Item $Blockers (Join-Path $MainOut "BLOCKERS.md") -Force
Copy-Item $Location (Join-Path $MainOut "LOCATION_EVIDENCE_SAMPLE.jsonl") -Force
Copy-Item $Perf (Join-Path $MainOut "PERF_SUMMARY.txt") -Force
Copy-Item $Safety (Join-Path $MainOut "SAFETY_SUMMARY.txt") -Force
git add "docs/chatgpt_handoff/cloud_ready_20260517" "docs/chatgpt_handoff/local_runner_queue/done" "docs/chatgpt_handoff/local_runner_queue/failed" "docs/chatgpt_handoff/local_runner_queue/outputs" 2>&1 | Tee-Object -FilePath $PublishLog
if(git diff --cached --name-only){ git commit -m "Publish ChatGPT cloud free executor reports" 2>&1 | Tee-Object -FilePath $PublishLog -Append; if($LASTEXITCODE -eq 0){ git push origin $ExpectedBranch 2>&1 | Tee-Object -FilePath $PublishLog -Append } }
Get-Content $Report
Get-Content $Blockers
