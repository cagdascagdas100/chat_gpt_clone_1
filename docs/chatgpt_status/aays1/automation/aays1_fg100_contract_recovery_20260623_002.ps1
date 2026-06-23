param([string]$RepoRoot='')
$TaskId='aays1_fg100_contract_recovery_20260623_002'
if(-not $RepoRoot){try{$RepoRoot=(git rev-parse --show-toplevel).Trim()}catch{$RepoRoot='C:\Users\cagda\Documents\GitHub\AAYS'}}
$statusPath=Join-Path $RepoRoot 'docs/chatgpt_status/aays1/status/aays1_fg100_contract_recovery_20260623_002_status.json'
$reportPath=Join-Path $RepoRoot 'docs/chatgpt_status/aays1/reports/aays1_fg100_contract_recovery_20260623_002_report.txt'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $statusPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $reportPath) | Out-Null
$required=@('england_map_web/app.js','terrayield_land_intelligence/app/schemas/future_growth.py','terrayield_land_intelligence/app/future_growth/evidence_service.py','terrayield_land_intelligence/app/future_growth/tile_service.py')
$missing=@();foreach($r in $required){if(-not(Test-Path(Join-Path $RepoRoot $r))){$missing+=$r}}
@{task_id=$TaskId;repo_root=$RepoRoot;missing=$missing;status='LOCAL_CONTRACT_DETECTED';progress_percent=70;final_ready_confirmed=$false;production_complete=$false}|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 $statusPath
"STATUS=LOCAL_CONTRACT_DETECTED`nTASK_ID=$TaskId`nMISSING_COUNT=$($missing.Count)`nPROGRESS_PERCENT=70`nFINAL_READY_CONFIRMED=false`nPRODUCTION_COMPLETE=false"|Set-Content -Encoding UTF8 $reportPath
if($missing.Count -gt 0){exit 2}else{exit 0}
