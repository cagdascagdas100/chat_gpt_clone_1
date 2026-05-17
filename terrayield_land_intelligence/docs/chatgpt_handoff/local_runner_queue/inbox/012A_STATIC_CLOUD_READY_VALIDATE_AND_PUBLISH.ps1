$ErrorActionPreference = "Continue"
$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$BranchExpected = "security-accuracy-expansion-20260508"
$OutDir = Join-Path $Repo "docs\chatgpt_handoff\cloud_ready_20260517"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Report = Join-Path $OutDir "012A_STATIC_CLOUD_READY_VALIDATE_REPORT.txt"
$Blockers = Join-Path $OutDir "012A_STATIC_CLOUD_READY_VALIDATE_BLOCKERS.md"
$ValidatorOut = Join-Path $OutDir "012A_STATIC_VALIDATOR_OUTPUT.json"
$PublishLog = Join-Path $OutDir "012A_PUBLISH_LOG.txt"
$B = New-Object System.Collections.Generic.List[string]
function AB($x){ if(-not $B.Contains($x)){ $B.Add($x) } }
Set-Location $Repo
$Before = (git branch --show-current).Trim()
git fetch origin $BranchExpected | Out-Null
git checkout $BranchExpected | Out-Null
git pull --ff-only origin $BranchExpected | Out-Null
$Branch = (git branch --show-current).Trim()
$Head = (git rev-parse --short=12 HEAD).Trim()
if($Branch -ne $BranchExpected){ AB "BRANCH_MISMATCH" }
$Required = @(
"Dockerfile.cloud",
"render.example.yaml",
".env.cloud.example",
"scripts\cloud_smoke_check.py",
"scripts\validate_cloud_readiness_static.py",
"docs\cloud_ready\INDEX_TR.md",
"docs\cloud_ready\FINAL_MANIFEST_20260517.json",
"docs\cloud_ready\PARALLEL_EXECUTION_BOARD_20260517.md",
"docs\chatgpt_handoff\cloud_ready_20260517\EXECUTION_REPORT.txt",
"docs\chatgpt_handoff\cloud_ready_20260517\BLOCKERS.md",
"docs\chatgpt_handoff\cloud_ready_20260517\LOCATION_EVIDENCE_SAMPLE.jsonl",
"docs\chatgpt_handoff\cloud_ready_20260517\PERF_SUMMARY.txt",
"docs\chatgpt_handoff\cloud_ready_20260517\SAFETY_SUMMARY.txt"
)
$Missing = @()
foreach($r in $Required){ if(-not(Test-Path (Join-Path $Repo $r))){ $Missing += $r } }
if($Missing.Count -gt 0){ AB ("MISSING_FILES:" + ($Missing -join ",")) }
$ValidatorStatus = "not_run"
if(Test-Path (Join-Path $Repo "scripts\validate_cloud_readiness_static.py")){
  $vo = python (Join-Path $Repo "scripts\validate_cloud_readiness_static.py") 2>&1
  $vo | Set-Content -LiteralPath $ValidatorOut -Encoding UTF8
  if($LASTEXITCODE -eq 0){ $ValidatorStatus="passed" } else { $ValidatorStatus="failed"; AB "STATIC_VALIDATOR_FAILED" }
}else{
  AB "STATIC_VALIDATOR_MISSING"
}
$Final = if($B.Count -eq 0){"CLOUD_READY_PENDING_PROVIDER"}else{"BLOCKED"}
$Next = if($B.Count -eq 0){"WAIT_FOR_USER_PROVIDER_DECISION"}else{$B[0]}
@(
"timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
"task=012A_STATIC_CLOUD_READY_VALIDATE_AND_PUBLISH",
"repo=$Repo",
"branch_before=$Before",
"checked_branch=$Branch",
"head=$Head",
"checked_files=$(if($Missing.Count -eq 0){'passed'}else{'failed'})",
"static_validator_status=$ValidatorStatus",
"public_url_verified=false",
"cloud_db_verified=false",
"final_classification=$Final",
"next_single_action=$Next",
"secret_values_printed=false",
"db_write=none",
"ddl=none",
"migration_apply=none",
"prod_deploy=none",
"blockers=$(if($B.Count -eq 0){'none'}else{($B -join ';')})"
) | Set-Content -LiteralPath $Report -Encoding UTF8
$BL=@("# 012A Blockers","")
if($B.Count -eq 0){$BL += "- none"}else{foreach($x in $B){$BL += "- $x"}}
$BL | Set-Content -LiteralPath $Blockers -Encoding UTF8
git add "docs/chatgpt_handoff/cloud_ready_20260517" 2>&1 | Tee-Object -FilePath $PublishLog
if(git diff --cached --name-only){ git commit -m "Publish 012A static cloud readiness validation" 2>&1 | Tee-Object -FilePath $PublishLog -Append; if($LASTEXITCODE -eq 0){ git push origin $BranchExpected 2>&1 | Tee-Object -FilePath $PublishLog -Append } }
Get-Content $Report
Get-Content $Blockers
