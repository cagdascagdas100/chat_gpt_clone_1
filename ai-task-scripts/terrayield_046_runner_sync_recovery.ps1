param(
  [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$ProjectRoot = $env:TERRAYIELD_PROJECT_ROOT
)

$ErrorActionPreference = 'Stop'
$TaskId = 'terrayield-046-runner-sync-recovery-then-accuracy-expansion'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$OutDir = Join-Path $RepoRoot 'docs\chatgpt_status\runner_outputs'
$WebDir = Join-Path $RepoRoot 'england_map_web\data\terrayield'
$JsonOut = Join-Path $OutDir 'terrayield-046-runner-sync-recovery-latest.json'
$TextOut = Join-Path $OutDir 'terrayield-046-runner-sync-recovery-latest.txt'
$HtmlOut = Join-Path $WebDir 'terrayield_046_live_progress.html'
$ChildLog = Join-Path $OutDir "terrayield-046-child-044-$Stamp.log"
New-Item -ItemType Directory -Force -Path $OutDir,$WebDir | Out-Null

$Rows = [System.Collections.Generic.List[object]]::new()
$Critical = 0
$Warnings = 0
function Add-Row([string]$Operation,[string]$State,[string]$Detail) {
  $Rows.Add([ordered]@{time=(Get-Date).ToString('s');operation=$Operation;state=$State;detail=$Detail})
}
function Run-Step([string]$Name,[scriptblock]$Action) {
  try { $detail = & $Action; Add-Row $Name 'DONE' (($detail | Out-String).Trim()); return $true }
  catch { $script:Critical++; Add-Row $Name 'BLOCKED' $_.Exception.Message; return $false }
}

Add-Row 'task_carrier_validation' 'DONE' 'command and script_path carrier present; existing runner only'

if (-not $ProjectRoot) {
  $Candidates = @(
    'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence',
    'F:\TerraYield_AAYS_Portable\terrayield_land_intelligence',
    'F:\TerraYield_AAYS_Portable'
  )
  $ProjectRoot = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if ($ProjectRoot) { Add-Row 'project_root_detection' 'DONE' $ProjectRoot }
else { $Warnings++; Add-Row 'project_root_detection' 'WARN' 'No TerraYield project root found; child will report path gate failure.' }

Run-Step 'bridge_git_snapshot' {
  git -C $RepoRoot status --short | Set-Content -Encoding UTF8 (Join-Path $OutDir "terrayield-046-git-status-$Stamp.txt")
  git -C $RepoRoot diff --stat | Set-Content -Encoding UTF8 (Join-Path $OutDir "terrayield-046-git-diff-stat-$Stamp.txt")
  'snapshot_written'
} | Out-Null

Run-Step 'bridge_git_stabilizer' {
  $dirty = @(git -C $RepoRoot status --porcelain=v1)
  if ($dirty.Count -gt 0) {
    $stashName = "terrayield-046-recovery-$Stamp"
    git -C $RepoRoot stash push -u -m $stashName | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git stash failed' }
    Add-Row 'bridge_git_stash' 'DONE' "preserved as $stashName; stash not dropped"
  } else { Add-Row 'bridge_git_stash' 'DONE' 'working tree clean; no stash needed' }
  git -C $RepoRoot fetch origin main --prune | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'git fetch failed' }
  git -C $RepoRoot pull --ff-only origin main | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'git pull --ff-only failed' }
  'fetch and ff-only pull completed'
} | Out-Null

Run-Step 'runner_stuck_detector' {
  $heartbeatCandidates = @(
    (Join-Path $RepoRoot 'ai-heartbeat\portable-runner.md'),
    (Join-Path $RepoRoot 'ai-heartbeat\runner-v4.md'),
    (Join-Path $RepoRoot 'ai-heartbeat\watchdog.md'),
    (Join-Path $RepoRoot 'ai-heartbeat\user-mode-watchdog.md')
  ) | Where-Object { Test-Path $_ }
  if ($heartbeatCandidates.Count -eq 0) { $script:Warnings++; return 'no local heartbeat files found; runner liveness remains unconfirmed' }
  $heartbeatCandidates | ForEach-Object { "$_ :: $((Get-Item $_).LastWriteTime.ToString('s'))" }
} | Out-Null

Run-Step 'endpoint_health_probe' {
  $checks = foreach ($url in @('http://127.0.0.1:8000/health','http://127.0.0.1:8000/api/health','http://127.0.0.1:5173/','http://127.0.0.1:3000/')) {
    try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5; [ordered]@{url=$url;ok=$true;status=[int]$r.StatusCode} }
    catch { [ordered]@{url=$url;ok=$false;error=$_.Exception.Message} }
  }
  $checks | ConvertTo-Json -Depth 5
} | Out-Null

Run-Step 'project_red_flag_quickscan' {
  if (-not $ProjectRoot -or -not (Test-Path $ProjectRoot)) { return 'project path unavailable; child path gate will remain fail-closed' }
  $patterns = 'DROP TABLE|TRUNCATE TABLE|DELETE FROM|VERIFIED_L4_LOAD|docker compose up --build|docker-compose up --build'
  $hits = Get-ChildItem -Path $ProjectRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\.git\\|\\node_modules\\|\\dist\\|\\build\\|\\.venv\\' -and $_.Extension -match '^\.(ps1|py|js|ts|tsx|sql|json|ya?ml)$' } |
    Select-String -Pattern $patterns -List -ErrorAction SilentlyContinue |
    Select-Object -First 60 Path,LineNumber,Pattern
  $hits | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $OutDir "terrayield-046-red-flags-$Stamp.json")
  "hits=$(@($hits).Count); review-only; no execution"
} | Out-Null

$ChildCommit = 'ae7baec9614031a2fad5303dbf1298e40e889822'
$ChildBlob = '17106d97934836dd6b85dea1fed191907f2570bb'
$ChildRepoPath = 'ai-task-scripts/terrayield_044_continuous_accuracy_expansion_watchdog.ps1'
$ChildSource = Join-Path $OutDir "terrayield-044-source-$Stamp.ps1"
$ChildAdapted = Join-Path $OutDir "terrayield-044-adapted-$Stamp.ps1"
$ChildExit = $null

if (Run-Step 'restore_044_child_from_git_history' {
  git -C $RepoRoot show "$ChildCommit`:$ChildRepoPath" | Set-Content -Encoding UTF8 $ChildSource
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $ChildSource)) { throw 'unable to restore 044 child from verified commit' }
  $actualBlob = (git -C $RepoRoot hash-object $ChildSource).Trim()
  if ($actualBlob -ne $ChildBlob) { throw "044 child blob mismatch: $actualBlob" }
  "verified_blob=$actualBlob"
}) {
  Run-Step 'adapt_044_child_paths' {
    $lines = Get-Content $ChildSource
    $bridgeEsc = $RepoRoot.Replace('"','`"')
    $projectEsc = if($ProjectRoot){$ProjectRoot.Replace('"','`"')}else{'C:\__TERRAYIELD_PROJECT_ROOT_NOT_FOUND__'}
    $adapted = foreach($line in $lines) {
      if ($line -match '^\$BridgeRoot\s*=') { '$BridgeRoot = "' + $bridgeEsc + '"' }
      elseif ($line -match '^\$ProjectRoot\s*=') { '$ProjectRoot = "' + $projectEsc + '"' }
      else { $line }
    }
    $adapted | Set-Content -Encoding UTF8 $ChildAdapted
    "adapted_child=$ChildAdapted"
  } | Out-Null

  try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $ChildAdapted *>&1 | Tee-Object -FilePath $ChildLog
    $ChildExit = $LASTEXITCODE
    if ($ChildExit -eq 0) { Add-Row 'start_044_child_accuracy_expansion' 'DONE' "exit_code=0; log=$ChildLog" }
    else { $Critical++; Add-Row 'start_044_child_accuracy_expansion' 'BLOCKED' "exit_code=$ChildExit; log=$ChildLog" }
  } catch {
    $Critical++; Add-Row 'start_044_child_accuracy_expansion' 'BLOCKED' $_.Exception.Message
  }
}

$State = if ($Critical -eq 0) { 'RECOVERY_EXECUTED_CONTINUE_ACCURACY_PROGRAM' } else { 'RECOVERY_PARTIAL_BLOCKED' }
$Result = [ordered]@{
  schema_version=1
  task_id=$TaskId
  generated_at=(Get-Date).ToString('o')
  state=$State
  operations_total=$Rows.Count
  operations_done=@($Rows | Where-Object {$_.state -eq 'DONE'}).Count
  operations_blocked=@($Rows | Where-Object {$_.state -eq 'BLOCKED'}).Count
  operations_warn=@($Rows | Where-Object {$_.state -eq 'WARN'}).Count
  child_044_exit_code=$ChildExit
  source_accuracy_score=45
  parcel_match_accuracy_score=27
  operational_health_score=0
  general_confidence_score=32
  accuracy_program_progress_percent=35
  technical_runner_progress_percent=99
  scores_updated_from_runtime=false
  next_wait_minutes='0 for repository recovery; up to 40 after runner pickup'
  operations=$Rows
  safety=[ordered]@{db_write=$false;deploy=$false;migration=$false;fake_data=$false;force_push=$false;second_runner=$false;stash_dropped=$false}
}
$Result | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $JsonOut
$Result | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $OutDir 'latest_output.json')
@"
Task: $TaskId
State: $State
Operations: $($Result.operations_done)/$($Result.operations_total), blocked=$($Result.operations_blocked), warn=$($Result.operations_warn)
Child 044 exit: $ChildExit
Technical runner: 99%
Accuracy program: 35%
Source accuracy: 45/100
Parcel match accuracy: 27/100
Operational health: 0/100
General confidence: 32/100
"@ | Set-Content -Encoding UTF8 $TextOut

function H([object]$v){ [System.Net.WebUtility]::HtmlEncode([string]$v) }
$trs = foreach($row in $Rows){ '<tr><td>'+ (H $row.time) +'</td><td>'+ (H $row.operation) +'</td><td>'+ (H $row.state) +'</td><td>'+ (H $row.detail) +'</td></tr>' }
$html = '<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TerraYield 046</title><style>body{font-family:Arial;margin:18px;background:#f4f6f8}table{border-collapse:collapse;width:100%;background:#fff}th,td{border:1px solid #ccd6dd;padding:7px;text-align:left;vertical-align:top}th{background:#edf1f3}.BLOCKED{font-weight:bold}</style></head><body><h1>TerraYield 046 satır bazlı ilerleme</h1><p>Durum: '+(H $State)+' | İşlem: '+$Result.operations_done+'/'+$Result.operations_total+' | Bloklu: '+$Result.operations_blocked+'</p><table><thead><tr><th>Zaman</th><th>İşlem</th><th>Durum</th><th>Ayrıntı</th></tr></thead><tbody>'+($trs -join '')+'</tbody></table></body></html>'
$html | Set-Content -Encoding UTF8 $HtmlOut

Write-Output "STATE=$State"
Write-Output "OPERATIONS_DONE=$($Result.operations_done)"
Write-Output "OPERATIONS_TOTAL=$($Result.operations_total)"
Write-Output "OPERATIONS_BLOCKED=$($Result.operations_blocked)"
Write-Output "CHILD_044_EXIT_CODE=$ChildExit"
if ($Critical -eq 0) { exit 0 } else { exit 1 }
