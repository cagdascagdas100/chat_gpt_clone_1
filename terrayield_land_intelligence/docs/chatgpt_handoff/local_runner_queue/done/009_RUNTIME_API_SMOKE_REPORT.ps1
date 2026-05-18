$ErrorActionPreference = "Continue"
$TaskName = "009_RUNTIME_API_SMOKE_REPORT"
$BranchExpected = "security-accuracy-expansion-20260508"
$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
$MainRepo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$OutDir = Join-Path $Repo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
$MainOut = Join-Path $MainRepo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
New-Item -ItemType Directory -Force -Path $OutDir,$MainOut | Out-Null
$Report = Join-Path $OutDir "009_RUNTIME_API_SMOKE_REPORT.txt"
$Blockers = Join-Path $OutDir "009_RUNTIME_API_SMOKE_BLOCKERS.md"
$Smoke = Join-Path $OutDir "009_RUNTIME_API_SMOKE.jsonl"
$Pytest = Join-Path $OutDir "009_RUNTIME_API_SMOKE_PYTEST.txt"
$Log = Join-Path $OutDir "009_RUNTIME_API_SMOKE_PUBLISH_LOG.txt"
$B = New-Object System.Collections.Generic.List[string]
function AB($x){ if(-not $B.Contains($x)){ $B.Add($x) } }
Set-Location $Repo
$Branch = (git branch --show-current).Trim()
$HeadBefore = (git rev-parse --short=12 HEAD).Trim()
if($Branch -ne $BranchExpected){ AB "BRANCH_MISMATCH:$Branch" }
git pull origin $BranchExpected | Out-Null
$PyOut = python -m pytest tests/test_parcel_matcher_source_confidence.py tests/test_source_confidence_integration.py tests/test_source_confidence_rules.py -q 2>&1
$PyExit = $LASTEXITCODE
@("pytest_exit_code=$PyExit", "", $PyOut) | Set-Content -LiteralPath $Pytest -Encoding UTF8
if($PyExit -ne 0){ AB "TARGETED_PYTEST_FAILED" }
$Base = "http://127.0.0.1:8010"
$Endpoints = @("/ops/storage-registry","/ops/consistency-check","/handoff/status","/map/listings?limit=1","/map/sales-history/combined?limit=1")
Remove-Item -LiteralPath $Smoke -Force -ErrorAction SilentlyContinue
$Ok=0; $Total=0
foreach($ep in $Endpoints){
  $Total += 1
  $url = $Base + $ep
  $status="error"; $code=""; $ms=""
  try{
    $sw=[Diagnostics.Stopwatch]::StartNew(); $r=Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 8; $sw.Stop()
    $code=[string]$r.StatusCode; $ms=[string][Math]::Round($sw.Elapsed.TotalMilliseconds,2)
    if($r.StatusCode -ge 200 -and $r.StatusCode -lt 500){ $status="ok"; $Ok+=1 }
  }catch{ $code="exception"; $ms="connection_or_timeout" }
  @{endpoint=$ep;status=$status;status_code=$code;elapsed_ms=$ms} | ConvertTo-Json -Compress | Add-Content -LiteralPath $Smoke -Encoding UTF8
}
if($Ok -lt 3){ AB "API_SMOKE_NOT_ENOUGH_OK" }
$Final = if($B.Count -eq 0){"RUNTIME_API_SMOKE_READY"}else{"BLOCKED"}
$Next = if($Final -eq "RUNTIME_API_SMOKE_READY"){"done"}else{$B[0]}
@(
"timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
"task=$TaskName",
"repo=$Repo",
"main_repo=$MainRepo",
"branch=$Branch",
"head_before=$HeadBefore",
"head_after=$((git rev-parse --short=12 HEAD).Trim())",
"pytest_exit_code=$PyExit",
"pytest_output=$Pytest",
"api_base_url=$Base",
"api_smoke_ok_count=$Ok",
"api_smoke_total=$Total",
"api_smoke_output=$Smoke",
"db_write=none",
"ddl=none",
"migration_apply=none",
"prod_deploy=none",
"secret_values_printed=false",
"final_classification=$Final",
"next_single_action=$Next"
) | Set-Content -LiteralPath $Report -Encoding UTF8
$BL=@("# 009 Runtime API Smoke Blockers","")
if($B.Count -eq 0){$BL += "- none"}else{foreach($x in $B){$BL += "- $x"}}
$BL | Set-Content -LiteralPath $Blockers -Encoding UTF8
Copy-Item $Report (Join-Path $MainOut "009_RUNTIME_API_SMOKE_REPORT.txt") -Force
Copy-Item $Blockers (Join-Path $MainOut "009_RUNTIME_API_SMOKE_BLOCKERS.md") -Force
Copy-Item $Smoke (Join-Path $MainOut "009_RUNTIME_API_SMOKE.jsonl") -Force -ErrorAction SilentlyContinue
Copy-Item $Pytest (Join-Path $MainOut "009_RUNTIME_API_SMOKE_PYTEST.txt") -Force -ErrorAction SilentlyContinue
git add "docs/chatgpt_handoff/parcel_location_evidence_wave_20260516" "docs/chatgpt_handoff/local_runner_queue/done" "docs/chatgpt_handoff/local_runner_queue/failed" "docs/chatgpt_handoff/local_runner_queue/outputs" 2>&1 | Tee-Object -FilePath $Log
if(git diff --cached --name-only){ git commit -m "Publish runtime API smoke report" 2>&1 | Tee-Object -FilePath $Log -Append; if($LASTEXITCODE -eq 0){ git push origin $Branch 2>&1 | Tee-Object -FilePath $Log -Append } }
Get-Content $Report
Get-Content $Blockers
