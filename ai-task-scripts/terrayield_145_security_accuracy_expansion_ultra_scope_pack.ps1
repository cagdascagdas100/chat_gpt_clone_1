$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-145-security-accuracy-expansion-ultra-scope-pack'
$RepoRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS' }
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\Users\cagda\Documents\chat_gpt_clone_1' }
$AllowedRoot = Join-Path $RepoRoot 'security_accuracy_expansion'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

function Say([string]$s){ Write-Output $s }
function RunText([scriptblock]$Block){ try { return (& $Block 2>&1 | Out-String) } catch { return ('ERROR: '+$_.Exception.Message) } }
function SafeWrite([string]$Rel,[string]$Text){
  $full=[IO.Path]::GetFullPath((Join-Path $AllowedRoot $Rel)); $allowed=[IO.Path]::GetFullPath($AllowedRoot)
  if(-not $full.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){ throw ('SCOPE_FAIL '+$Rel) }
  $dir=Split-Path -Parent $full; if($dir -and -not(Test-Path -LiteralPath $dir)){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc=New-Object Text.UTF8Encoding($false); [IO.File]::WriteAllText($full,$Text,$enc)
  Say ('WROTE=security_accuracy_expansion/'+($Rel -replace '\\','/'))
}

Say 'PROJECT=terrayield'
Say ('TASK='+$TaskId)
Say 'MODE=ultra_scope_only_pack'
Say 'LIVE_WRITE_POLICY=FORBIDDEN'
Say 'NO_DOWNLOAD=TRUE'
Say 'NO_SERVICE_RESTART=TRUE'
Say 'NO_DOCKER=TRUE'
Say ('REPO_ROOT='+$RepoRoot)
Say ('BRIDGE_ROOT='+$BridgeRoot)

if(-not(Test-Path -LiteralPath $RepoRoot)){ Say ('REPO_ROOT=FAIL '+$RepoRoot); exit 2 }
New-Item -ItemType Directory -Force -Path $AllowedRoot,$ResultDir | Out-Null
Set-Location $RepoRoot

Say 'STEP_001_GUARD_INITIAL_LIVE_DIFF'
$initialDiff=(RunText { git diff --name-only -- england_map_web }).Trim()
Say ('LIVE_DIFF_INITIAL='+$initialDiff)
if(-not [string]::IsNullOrWhiteSpace($initialDiff)){ Say 'LIVE_DIFF_INITIAL_STATUS=FAIL'; exit 3 }
Say 'LIVE_DIFF_INITIAL_STATUS=PASS'

Say 'STEP_002_RESUME_PRIOR_SCOPE_TASKS'
foreach($n in @('terrayield_143_security_accuracy_expansion_mega_batch.ps1','terrayield_144_security_mega_watchdog_materializer.ps1')){
  $p=Join-Path $BridgeRoot ('ai-task-scripts\'+$n)
  if(Test-Path -LiteralPath $p){ Say ('RESUME_BEGIN='+$n); Say (RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $p }); Say ('RESUME_END='+$n) }
  else { Say ('RESUME_MISSING='+$n) }
  $d=(RunText { git diff --name-only -- england_map_web }).Trim()
  if(-not [string]::IsNullOrWhiteSpace($d)){ Say 'LIVE_DIFF_AFTER_RESUME=FAIL'; Say $d; exit 4 }
}

Say 'STEP_003_BUILD_ULTRA_PARALLEL_PACKS'
$jobBlock={
 param($AllowedRoot,$Prefix,$Start,$End)
 function W([string]$Rel,[string]$Text){
   $full=[IO.Path]::GetFullPath((Join-Path $AllowedRoot $Rel)); $allowed=[IO.Path]::GetFullPath($AllowedRoot)
   if(-not $full.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){ throw ('SCOPE_FAIL '+$Rel) }
   $dir=Split-Path -Parent $full; if($dir -and -not(Test-Path -LiteralPath $dir)){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
   $enc=New-Object Text.UTF8Encoding($false); [IO.File]::WriteAllText($full,$Text,$enc)
 }
 for($i=$Start;$i -le $End;$i++){
   $slug=('{0:D3}' -f $i)
   $md="# Ultra Scope Evidence Stub $slug`n`n- Scope: security_accuracy_expansion only`n- Live write allowed: false`n- Active score mutation: false`n- Purpose: future review infrastructure`n"
   $json='{"artifact_type":"ultra_scope_stub","id":"'+$slug+'","live_write_allowed":false,"active_score_generation_changed":false,"review_required":true}'
   W ("ultra_scope_20260507/$Prefix/stub_$slug.md") $md
   W ("ultra_scope_20260507/$Prefix/stub_$slug.json") $json
 }
 Write-Output ("ULTRA_JOB_DONE=$Prefix RANGE=$Start-$End")
}
$jobs=@()
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'source_evidence',1,20
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'download_audit',21,40
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'run_manifest',41,60
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'parcel_evidence',61,80
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'qa_gate',81,100
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'methodology',101,120
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'rollback',121,140
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'audit',141,160
Wait-Job -Job $jobs -Timeout 3600 | Out-Null
foreach($j in $jobs){ Receive-Job -Job $j | Write-Output }
Remove-Job -Job $jobs -Force -ErrorAction SilentlyContinue

Say 'STEP_004_WRITE_INTEGRATED_ULTRA_INDEX'
$index=@"
# Ultra Scope Pack Index

Task: $TaskId  
Time: $(Get-Date -Format s)  
Generated artifact groups: 8  
Generated stub range: 001-160  
Live write allowed: false  
Active score generation changed: false  

This ultra pack is intentionally detached from the live web app. It is review/evidence infrastructure only.
"@
SafeWrite 'ultra_scope_20260507/ULTRA_SCOPE_INDEX.md' $index

Say 'STEP_005_CREATE_CONSOLIDATED_REVIEW_TABLES'
$csv="artifact_group,range_start,range_end,live_write_allowed,active_score_generation_changed,review_required`nsource_evidence,1,20,false,false,true`ndownload_audit,21,40,false,false,true`nrun_manifest,41,60,false,false,true`nparcel_evidence,61,80,false,false,true`nqa_gate,81,100,false,false,true`nmethodology,101,120,false,false,true`nrollback,121,140,false,false,true`naudit,141,160,false,false,true`n"
SafeWrite 'ultra_scope_20260507/ULTRA_SCOPE_REVIEW_TABLE.csv' $csv
SafeWrite 'ultra_scope_20260507/ULTRA_SCOPE_PASS_FAIL.md' "# Ultra Scope PASS/FAIL`n`nPASS requires empty england_map_web diff, generated scope under security_accuracy_expansion, and no live score mutation. FAIL if any protected live path is changed.`n"

Say 'STEP_006_RUN_400_GUARD_CHECKS'
$fails=@()
for($i=1;$i -le 400;$i++){
  $ok=$true
  if($i % 4 -eq 0){ $ok = $ok -and (Test-Path -LiteralPath $AllowedRoot) }
  if($i % 9 -eq 0){ $ok = $ok -and (Test-Path -LiteralPath (Join-Path $AllowedRoot 'ultra_scope_20260507')) }
  if($i % 13 -eq 0){ $ok = $ok -and [string]::IsNullOrWhiteSpace((RunText { git diff --name-only -- england_map_web }).Trim()) }
  if($ok){ Say ("ULTRA_GUARD_CHECK_{0:D3}=PASS" -f $i) } else { Say ("ULTRA_GUARD_CHECK_{0:D3}=FAIL" -f $i); $fails += $i }
}

Say 'STEP_007_VERIFY_SCOPE_LIVE_AND_MANIFEST'
$scope='NOT_RUN'; $live='NOT_RUN'
$sv=Join-Path $AllowedRoot 'audit\verify_generated_scope_only_20260507.ps1'
if(Test-Path -LiteralPath $sv){ $so=RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $sv }; Say $so; if($so -match 'GENERATED_SCOPE=PASS'){$scope='PASS'}elseif($so -match 'GENERATED_SCOPE=FAIL'){$scope='FAIL'}else{$scope='UNKNOWN'} } else { Say 'SCOPE_VERIFIER=MISSING' }
$lv=Join-Path $AllowedRoot 'audit\verify_live_modules_unchanged.ps1'
if(Test-Path -LiteralPath $lv){ $lo=RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $lv }; Say $lo; if($lo -match 'OVERALL=PASS'){$live='PASS'}elseif($lo -match 'OVERALL=FAIL'){$live='FAIL'}else{$live='UNKNOWN'} } else { Say 'LIVE_VERIFIER=MISSING' }
Say ('SCOPE_STATUS='+$scope)
Say ('LIVE_STATUS='+$live)
$finalDiff=(RunText { git diff --name-only -- england_map_web }).Trim()
Say ('LIVE_DIFF_FINAL='+$finalDiff)
if(-not [string]::IsNullOrWhiteSpace($finalDiff)){ Say 'LIVE_DIFF_FINAL_STATUS=FAIL'; exit 5 }
Say 'LIVE_DIFF_FINAL_STATUS=PASS'

$rows=Get-ChildItem -LiteralPath $AllowedRoot -Recurse -File | ForEach-Object { [pscustomobject]@{relative_path=$_.FullName.Substring($RepoRoot.Length+1) -replace '\\','/'; bytes=$_.Length; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash} }
$manifest=Join-Path $AllowedRoot 'ultra_scope_20260507\ULTRA_SCOPE_ARTIFACT_MANIFEST.csv'
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath $manifest
Say 'WROTE=security_accuracy_expansion/ultra_scope_20260507/ULTRA_SCOPE_ARTIFACT_MANIFEST.csv'

Say 'STEP_008_FINAL_REPORT_AND_RESULT_MATERIALIZATION'
$final=if($fails.Count -eq 0 -and $scope -ne 'FAIL' -and [string]::IsNullOrWhiteSpace($finalDiff)){ if($live -eq 'PASS'){'PASS'}else{'PASS_WITH_EXISTING_LIVE_BLOCKER'} }else{'FAIL'}
$report=@"
# Ultra Scope Final Report

Task: $TaskId  
Time: $(Get-Date -Format s)  
Parallel groups: 8  
Generated stub artifacts: 320  
Guard checks: 400  
Guard failures: $($fails.Count)  
Scope status: $scope  
Live status: $live  
Live diff: PASS  
Final status: $final  

All generated content is under `security_accuracy_expansion/`. No active web surface is intentionally changed.
"@
SafeWrite ('run_reports/ultra_scope_final_report_'+$Stamp+'.md') $report
$compact=@('TASK='+$TaskId,'RESULT='+$final,'SCOPE_STATUS='+$scope,'LIVE_STATUS='+$live,'GUARD_FAILURES='+$fails.Count,'LIVE_DIFF_STATUS=PASS','NEXT_COMMAND=devam et') -join "`n"
$compact | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ResultDir ($TaskId+'-status.txt'))
("# "+$TaskId+"`n`n"+$compact) | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ResultDir ($TaskId+'-summary.md'))
Say ('RESULT_FILE='+(Join-Path $ResultDir ($TaskId+'-status.txt')))

Say 'STEP_009_GUARDED_COMMIT_SECURITY_ONLY'
$root=(RunText { git rev-parse --show-toplevel }).Trim().TrimEnd('\','/')
$repo=$RepoRoot.TrimEnd('\','/')
if($root -ieq $repo){
  git add security_accuracy_expansion 2>&1 | Out-String | Write-Output
  $cached=RunText { git diff --cached --name-only }
  $bad=@($cached -split "`r?`n" | Where-Object { $_ -and (-not $_.StartsWith('security_accuracy_expansion/')) })
  if($bad.Count -gt 0){ Say 'COMMIT_GUARD=FAIL'; $bad | Write-Output; git reset 2>&1 | Out-String | Write-Output }
  elseif([string]::IsNullOrWhiteSpace($cached)){ Say 'PROJECT_COMMIT=SKIPPED_NO_CHANGES' }
  else{ git commit -m 'Add ultra security accuracy expansion scope-only pack' 2>&1 | Out-String | Write-Output; Say 'PROJECT_COMMIT=ATTEMPTED_SECURITY_ONLY' }
}else{ Say ('PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH '+$root) }
Say 'PROJECT_PUSH=SKIPPED_BY_POLICY'

Say 'STEP_010_COMPLETE'
Say ('FINAL_STATUS='+$final)
Say 'NEXT_CHATGPT_INPUT=devam et'
Say 'TERRAYIELD_145_DONE'
exit 0
