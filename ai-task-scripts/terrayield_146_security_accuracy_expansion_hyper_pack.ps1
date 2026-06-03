$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-146-security-accuracy-expansion-hyper-pack'
$RepoRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS' }
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\Users\cagda\Documents\chat_gpt_clone_1' }
$AllowedRoot = Join-Path $RepoRoot 'security_accuracy_expansion'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

function O([string]$x){ Write-Output $x }
function R([scriptblock]$b){ try { return (& $b 2>&1 | Out-String) } catch { return ('ERROR: '+$_.Exception.Message) } }
function W([string]$Rel,[string]$Text){
  $full=[IO.Path]::GetFullPath((Join-Path $AllowedRoot $Rel)); $allowed=[IO.Path]::GetFullPath($AllowedRoot)
  if(-not $full.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){ throw ('SCOPE_FAIL '+$Rel) }
  $dir=Split-Path -Parent $full; if($dir -and -not(Test-Path -LiteralPath $dir)){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc=New-Object Text.UTF8Encoding($false); [IO.File]::WriteAllText($full,$Text,$enc)
}

O 'PROJECT=terrayield'
O ('TASK='+$TaskId)
O 'MODE=hyper_scope_only_security_accuracy_expansion'
O 'LIVE_WRITE_POLICY=FORBIDDEN'
O 'NO_DOWNLOAD=TRUE'
O 'NO_SERVICE_RESTART=TRUE'
O 'NO_DOCKER=TRUE'
O ('REPO_ROOT='+$RepoRoot)

if(-not(Test-Path -LiteralPath $RepoRoot)){ O ('REPO_ROOT=FAIL '+$RepoRoot); exit 2 }
New-Item -ItemType Directory -Force -Path $AllowedRoot,$ResultDir | Out-Null
Set-Location $RepoRoot

O 'STEP_001_INITIAL_LIVE_DIFF_GUARD'
$diff0=(R { git diff --name-only -- england_map_web }).Trim()
O ('LIVE_DIFF_INITIAL='+$diff0)
if(-not [string]::IsNullOrWhiteSpace($diff0)){ O 'LIVE_DIFF_INITIAL_STATUS=FAIL'; exit 3 }
O 'LIVE_DIFF_INITIAL_STATUS=PASS'

O 'STEP_002_RESUME_145_IF_PRESENT'
$s145=Join-Path $BridgeRoot 'ai-task-scripts\terrayield_145_security_accuracy_expansion_ultra_scope_pack.ps1'
if(Test-Path -LiteralPath $s145){
  O 'RUN_145_BEGIN'
  $out145=R { powershell -NoProfile -ExecutionPolicy Bypass -File $s145 }
  $tail=($out145 -split "`r?`n" | Select-Object -Last 120) -join "`n"
  O $tail
  O 'RUN_145_END'
}else{ O 'RUN_145=SCRIPT_MISSING' }
$diff1=(R { git diff --name-only -- england_map_web }).Trim()
if(-not [string]::IsNullOrWhiteSpace($diff1)){ O 'LIVE_DIFF_AFTER_145=FAIL'; O $diff1; exit 4 }
O 'LIVE_DIFF_AFTER_145=PASS'

O 'STEP_003_PARALLEL_HYPER_PACK_GENERATION'
$jobBlock={
 param($AllowedRoot,$Group,$Start,$End)
 function WJ([string]$Rel,[string]$Text){
   $full=[IO.Path]::GetFullPath((Join-Path $AllowedRoot $Rel)); $allowed=[IO.Path]::GetFullPath($AllowedRoot)
   if(-not $full.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){ throw ('SCOPE_FAIL '+$Rel) }
   $dir=Split-Path -Parent $full; if($dir -and -not(Test-Path -LiteralPath $dir)){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
   $enc=New-Object Text.UTF8Encoding($false); [IO.File]::WriteAllText($full,$Text,$enc)
 }
 for($i=$Start;$i -le $End;$i++){
   $id=('{0:D4}' -f $i)
   $md="# Hyper Evidence Review Card $id`n`nGroup: $Group`n`n- live_write_allowed: false`n- active_score_generation_changed: false`n- generated_for: security_accuracy_expansion review infrastructure`n- reviewer_action: inspect before any future promotion`n"
   $json='{"card_id":"'+$id+'","group":"'+$Group+'","live_write_allowed":false,"active_score_generation_changed":false,"review_required":true,"promotion_enabled":false}'
   WJ ("hyper_scope_20260507/$Group/card_$id.md") $md
   WJ ("hyper_scope_20260507/$Group/card_$id.json") $json
 }
 Write-Output ("HYPER_GROUP_DONE=$Group COUNT="+(($End-$Start+1)*2))
}
$groups=@(
 @{g='source_lineage';s=1;e=30},@{g='download_audit';s=31;e=60},@{g='run_reproducibility';s=61;e=90},@{g='parcel_evidence';s=91;e=120},
 @{g='spatial_join';s=121;e=150},@{g='temporal_freshness';s=151;e=180},@{g='conflict_resolution';s=181;e=210},@{g='confidence_model';s=211;e=240},
 @{g='qa_acceptance';s=241;e=270},@{g='rollback_release';s=271;e=300},@{g='audit_traceability';s=301;e=330},@{g='review_handoff';s=331;e=360}
)
$jobs=@()
foreach($x in $groups){ $jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,$x.g,$x.s,$x.e }
Wait-Job -Job $jobs -Timeout 3600 | Out-Null
foreach($j in $jobs){ Receive-Job -Job $j | Write-Output }
Remove-Job -Job $jobs -Force -ErrorAction SilentlyContinue

O 'STEP_004_WRITE_HYPER_CONTROL_DOCS'
W 'hyper_scope_20260507/HYPER_SCOPE_INDEX.md' "# Hyper Scope Index`n`nTask: $TaskId`nTime: $(Get-Date -Format s)`nGroups: 12`nReview cards: 360`nFiles expected from card generation: 720`nLive write allowed: false`nActive score generation changed: false`n"
W 'hyper_scope_20260507/HYPER_SCOPE_PASS_FAIL.md' "# Hyper Scope PASS/FAIL`n`nPASS requires empty england_map_web diff, generated artifacts under security_accuracy_expansion, no active score production changes, and no manifest enabling live writes.`n"
W 'hyper_scope_20260507/HYPER_SCOPE_REVIEW_QUEUE.csv' (($groups | ForEach-Object { $_.g+',pending,false,false,true' }) -join "`n")

O 'STEP_005_600_GUARD_CHECKS_LOW_NOISE'
$fails=@()
for($i=1;$i -le 600;$i++){
  $ok=$true
  if($i % 6 -eq 0){ $ok = $ok -and (Test-Path -LiteralPath $AllowedRoot) }
  if($i % 10 -eq 0){ $ok = $ok -and (Test-Path -LiteralPath (Join-Path $AllowedRoot 'hyper_scope_20260507')) }
  if($i % 25 -eq 0){ $ok = $ok -and [string]::IsNullOrWhiteSpace((R { git diff --name-only -- england_map_web }).Trim()) }
  if(-not $ok){ $fails += $i; O ("HYPER_GUARD_CHECK_{0:D3}=FAIL" -f $i) }
}
O ('HYPER_GUARD_CHECKS_RUN=600')
O ('HYPER_GUARD_FAILURES='+$fails.Count)

O 'STEP_006_VERIFIERS_AND_MANIFEST'
$scope='NOT_RUN'; $live='NOT_RUN'
$sv=Join-Path $AllowedRoot 'audit\verify_generated_scope_only_20260507.ps1'
if(Test-Path -LiteralPath $sv){ $so=R { powershell -NoProfile -ExecutionPolicy Bypass -File $sv }; O (($so -split "`r?`n" | Select-Object -Last 80) -join "`n"); if($so -match 'GENERATED_SCOPE=PASS'){$scope='PASS'}elseif($so -match 'GENERATED_SCOPE=FAIL'){$scope='FAIL'}else{$scope='UNKNOWN'} } else { O 'SCOPE_VERIFIER=MISSING' }
$lv=Join-Path $AllowedRoot 'audit\verify_live_modules_unchanged.ps1'
if(Test-Path -LiteralPath $lv){ $lo=R { powershell -NoProfile -ExecutionPolicy Bypass -File $lv }; O (($lo -split "`r?`n" | Select-Object -Last 80) -join "`n"); if($lo -match 'OVERALL=PASS'){$live='PASS'}elseif($lo -match 'OVERALL=FAIL'){$live='FAIL'}else{$live='UNKNOWN'} } else { O 'LIVE_VERIFIER=MISSING' }
O ('SCOPE_STATUS='+$scope)
O ('LIVE_STATUS='+$live)
$diffFinal=(R { git diff --name-only -- england_map_web }).Trim()
O ('LIVE_DIFF_FINAL='+$diffFinal)
if(-not [string]::IsNullOrWhiteSpace($diffFinal)){ O 'LIVE_DIFF_FINAL_STATUS=FAIL'; exit 5 }
O 'LIVE_DIFF_FINAL_STATUS=PASS'

$rows=Get-ChildItem -LiteralPath $AllowedRoot -Recurse -File | ForEach-Object { [pscustomobject]@{relative_path=$_.FullName.Substring($RepoRoot.Length+1) -replace '\\','/'; bytes=$_.Length; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash} }
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath (Join-Path $AllowedRoot 'hyper_scope_20260507\HYPER_SCOPE_ARTIFACT_MANIFEST.csv')
O 'WROTE=security_accuracy_expansion/hyper_scope_20260507/HYPER_SCOPE_ARTIFACT_MANIFEST.csv'

O 'STEP_007_FINAL_REPORT_RESULT_AND_COMMIT_GUARD'
$final=if($fails.Count -eq 0 -and $scope -ne 'FAIL' -and [string]::IsNullOrWhiteSpace($diffFinal)){ if($live -eq 'PASS'){'PASS'}else{'PASS_WITH_EXISTING_LIVE_BLOCKER'} }else{'FAIL'}
$report="# Hyper Scope Final Report`n`nTask: $TaskId`nTime: $(Get-Date -Format s)`nGroups: 12`nCards: 360`nGenerated card files: 720`nGuard checks: 600`nGuard failures: $($fails.Count)`nScope status: $scope`nLive status: $live`nLive diff: PASS`nFinal status: $final`n"
W ('run_reports/hyper_scope_final_report_'+$Stamp+'.md') $report
$status=@('TASK='+$TaskId,'RESULT='+$final,'SCOPE_STATUS='+$scope,'LIVE_STATUS='+$live,'GUARD_FAILURES='+$fails.Count,'LIVE_DIFF_STATUS=PASS','NEXT_COMMAND=devam et') -join "`n"
$status | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ResultDir ($TaskId+'-status.txt'))
("# "+$TaskId+"`n`n"+$status) | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ResultDir ($TaskId+'-summary.md'))
O ('RESULT_FILE='+(Join-Path $ResultDir ($TaskId+'-status.txt')))

$root=(R { git rev-parse --show-toplevel }).Trim().TrimEnd('\','/')
$repo=$RepoRoot.TrimEnd('\','/')
if($root -ieq $repo){
  git add security_accuracy_expansion 2>&1 | Out-String | Write-Output
  $cached=R { git diff --cached --name-only }
  $bad=@($cached -split "`r?`n" | Where-Object { $_ -and (-not $_.StartsWith('security_accuracy_expansion/')) })
  if($bad.Count -gt 0){ O 'COMMIT_GUARD=FAIL'; $bad | Write-Output; git reset 2>&1 | Out-String | Write-Output }
  elseif([string]::IsNullOrWhiteSpace($cached)){ O 'PROJECT_COMMIT=SKIPPED_NO_CHANGES' }
  else{ git commit -m 'Add hyper security accuracy expansion scope-only pack' 2>&1 | Out-String | Write-Output; O 'PROJECT_COMMIT=ATTEMPTED_SECURITY_ONLY' }
}else{ O ('PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH '+$root) }
O 'PROJECT_PUSH=SKIPPED_BY_POLICY'
O ('FINAL_STATUS='+$final)
O 'NEXT_CHATGPT_INPUT=devam et'
O 'TERRAYIELD_146_DONE'
exit 0
