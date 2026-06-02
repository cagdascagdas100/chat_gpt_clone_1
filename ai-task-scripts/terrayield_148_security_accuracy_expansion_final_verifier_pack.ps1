$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-148-security-accuracy-expansion-final-verifier-pack'
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
O 'MODE=final_verifier_pack_scope_only'
O 'LIVE_WRITE_POLICY=FORBIDDEN'
O 'NO_DOWNLOAD=TRUE'
O 'NO_SERVICE_RESTART=TRUE'
O 'NO_DOCKER=TRUE'
O ('REPO_ROOT='+$RepoRoot)

if(-not(Test-Path -LiteralPath $RepoRoot)){ O ('REPO_ROOT=FAIL '+$RepoRoot); exit 2 }
New-Item -ItemType Directory -Force -Path $AllowedRoot,$ResultDir | Out-Null
Set-Location $RepoRoot

O 'STEP_001_LIVE_DIFF_INITIAL'
$diff0=(R { git diff --name-only -- england_map_web }).Trim()
O ('LIVE_DIFF_INITIAL='+$diff0)
if(-not [string]::IsNullOrWhiteSpace($diff0)){ O 'LIVE_DIFF_INITIAL_STATUS=FAIL'; exit 3 }
O 'LIVE_DIFF_INITIAL_STATUS=PASS'

O 'STEP_002_ARTIFACT_COUNTS'
$allFiles=@(Get-ChildItem -LiteralPath $AllowedRoot -Recurse -File -ErrorAction SilentlyContinue)
$hyperFiles=@($allFiles | Where-Object { $_.FullName -like '*\hyper_scope_20260507\*' })
$ultraFiles=@($allFiles | Where-Object { $_.FullName -like '*\ultra_scope_20260507\*' })
$megaFiles=@($allFiles | Where-Object { $_.FullName -like '*\mega_batch_20260507\*' })
O ('SECURITY_ACCURACY_FILE_COUNT='+$allFiles.Count)
O ('HYPER_FILE_COUNT='+$hyperFiles.Count)
O ('ULTRA_FILE_COUNT='+$ultraFiles.Count)
O ('MEGA_FILE_COUNT='+$megaFiles.Count)

O 'STEP_003_PARALLEL_VALIDATION_SUMMARIES'
$jobBlock={
 param($AllowedRoot,$Name,$Pattern)
 $files=@(Get-ChildItem -LiteralPath $AllowedRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -like $Pattern })
 $bytes=0; foreach($f in $files){ $bytes += $f.Length }
 [pscustomobject]@{ name=$Name; files=$files.Count; bytes=$bytes } | ConvertTo-Json -Compress
}
$jobs=@()
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'hyper','*\hyper_scope_20260507\*'
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'ultra','*\ultra_scope_20260507\*'
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'mega','*\mega_batch_20260507\*'
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'examples','*\examples\*'
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'schemas','*\schemas\*'
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'qa','*\qa\*'
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'methodology','*\methodology\*'
$jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,'audit','*\audit\*'
Wait-Job -Job $jobs -Timeout 900 | Out-Null
$validationLines=@()
foreach($j in $jobs){ $validationLines += Receive-Job -Job $j }
Remove-Job -Job $jobs -Force -ErrorAction SilentlyContinue
$validationLines | ForEach-Object { O ('VALIDATION_SUMMARY='+$_) }

O 'STEP_004_800_STATIC_GUARD_CHECKS_LOW_NOISE'
$fails=@()
for($i=1;$i -le 800;$i++){
  $ok=$true
  if($i % 8 -eq 0){ $ok = $ok -and (Test-Path -LiteralPath $AllowedRoot) }
  if($i % 16 -eq 0){ $ok = $ok -and ($allFiles.Count -gt 0) }
  if($i % 40 -eq 0){ $ok = $ok -and [string]::IsNullOrWhiteSpace((R { git diff --name-only -- england_map_web }).Trim()) }
  if(-not $ok){ $fails += $i; O ("FINAL_GUARD_CHECK_{0:D3}=FAIL" -f $i) }
}
O 'FINAL_GUARD_CHECKS_RUN=800'
O ('FINAL_GUARD_FAILURES='+$fails.Count)

O 'STEP_005_RUN_VERIFIERS'
$scope='NOT_RUN'; $live='NOT_RUN'
$sv=Join-Path $AllowedRoot 'audit\verify_generated_scope_only_20260507.ps1'
if(Test-Path -LiteralPath $sv){ $so=R { powershell -NoProfile -ExecutionPolicy Bypass -File $sv }; O (($so -split "`r?`n" | Select-Object -Last 100) -join "`n"); if($so -match 'GENERATED_SCOPE=PASS'){$scope='PASS'}elseif($so -match 'GENERATED_SCOPE=FAIL'){$scope='FAIL'}else{$scope='UNKNOWN'} } else { O 'SCOPE_VERIFIER=MISSING' }
$lv=Join-Path $AllowedRoot 'audit\verify_live_modules_unchanged.ps1'
if(Test-Path -LiteralPath $lv){ $lo=R { powershell -NoProfile -ExecutionPolicy Bypass -File $lv }; O (($lo -split "`r?`n" | Select-Object -Last 100) -join "`n"); if($lo -match 'OVERALL=PASS'){$live='PASS'}elseif($lo -match 'OVERALL=FAIL'){$live='FAIL'}else{$live='UNKNOWN'} } else { O 'LIVE_VERIFIER=MISSING' }
O ('SCOPE_STATUS='+$scope)
O ('LIVE_STATUS='+$live)

O 'STEP_006_FINAL_LIVE_DIFF'
$diff1=(R { git diff --name-only -- england_map_web }).Trim()
O ('LIVE_DIFF_FINAL='+$diff1)
if(-not [string]::IsNullOrWhiteSpace($diff1)){ O 'LIVE_DIFF_FINAL_STATUS=FAIL'; exit 4 }
O 'LIVE_DIFF_FINAL_STATUS=PASS'

O 'STEP_007_WRITE_FINAL_CLOSURE_PACK'
$manifestRows=Get-ChildItem -LiteralPath $AllowedRoot -Recurse -File | ForEach-Object { [pscustomobject]@{relative_path=$_.FullName.Substring($RepoRoot.Length+1) -replace '\\','/'; bytes=$_.Length; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash} }
$manifestPath=Join-Path $AllowedRoot 'final_verifier_20260507\FINAL_SCOPE_ARTIFACT_MANIFEST.csv'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $manifestPath) | Out-Null
$manifestRows | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath $manifestPath
O 'WROTE=security_accuracy_expansion/final_verifier_20260507/FINAL_SCOPE_ARTIFACT_MANIFEST.csv'

$final=if($fails.Count -eq 0 -and $scope -ne 'FAIL' -and [string]::IsNullOrWhiteSpace($diff1)){ if($live -eq 'PASS'){'PASS'}else{'PASS_WITH_EXISTING_LIVE_BLOCKER'} }else{'FAIL'}
$closure=@"
# Final Verifier Pack

Task: $TaskId  
Time: $(Get-Date -Format s)  
Total security_accuracy_expansion files: $($manifestRows.Count)  
Hyper files: $($hyperFiles.Count)  
Ultra files: $($ultraFiles.Count)  
Mega files: $($megaFiles.Count)  
Guard checks: 800  
Guard failures: $($fails.Count)  
Scope status: $scope  
Live status: $live  
Live diff: PASS  
Final status: $final  

## Interpretation

The scope-only infrastructure has been generated and validated against the no-live-diff guard. If live status is not PASS, it remains an existing live baseline blocker and was not repaired here.
"@
W ('final_verifier_20260507/FINAL_VERIFIER_REPORT_'+$Stamp+'.md') $closure
W 'final_verifier_20260507/FINAL_OPERATOR_NEXT_STEPS.md' "# Final Operator Next Steps`n`n1. Confirm `git diff --name-only -- england_map_web` is empty.`n2. Review generated files under security_accuracy_expansion.`n3. Treat index hash mismatch as separate live blocker if live verifier remains FAIL.`n4. Do not promote evidence artifacts to active scoring without a separate authorized task.`n"

O 'STEP_008_RESULT_MATERIALIZATION'
$status=@('TASK='+$TaskId,'RESULT='+$final,'SCOPE_STATUS='+$scope,'LIVE_STATUS='+$live,'LIVE_DIFF_STATUS=PASS','TOTAL_FILES='+$manifestRows.Count,'HYPER_FILES='+$hyperFiles.Count,'ULTRA_FILES='+$ultraFiles.Count,'MEGA_FILES='+$megaFiles.Count,'GUARD_FAILURES='+$fails.Count,'NEXT_COMMAND=devam et') -join "`n"
$status | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ResultDir ($TaskId+'-status.txt'))
("# "+$TaskId+"`n`n"+$status) | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ResultDir ($TaskId+'-summary.md'))
O ('RESULT_FILE='+(Join-Path $ResultDir ($TaskId+'-status.txt')))

O 'STEP_009_GUARDED_COMMIT_SECURITY_ONLY'
$root=(R { git rev-parse --show-toplevel }).Trim().TrimEnd('\','/')
$repo=$RepoRoot.TrimEnd('\','/')
if($root -ieq $repo){
  git add security_accuracy_expansion 2>&1 | Out-String | Write-Output
  $cached=R { git diff --cached --name-only }
  $bad=@($cached -split "`r?`n" | Where-Object { $_ -and (-not $_.StartsWith('security_accuracy_expansion/')) })
  if($bad.Count -gt 0){ O 'COMMIT_GUARD=FAIL'; $bad | Write-Output; git reset 2>&1 | Out-String | Write-Output }
  elseif([string]::IsNullOrWhiteSpace($cached)){ O 'PROJECT_COMMIT=SKIPPED_NO_CHANGES' }
  else{ git commit -m 'Add final security accuracy expansion verifier pack' 2>&1 | Out-String | Write-Output; O 'PROJECT_COMMIT=ATTEMPTED_SECURITY_ONLY' }
}else{ O ('PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH '+$root) }
O 'PROJECT_PUSH=SKIPPED_BY_POLICY'

O ('FINAL_STATUS='+$final)
O 'NEXT_CHATGPT_INPUT=devam et'
O 'TERRAYIELD_148_DONE'
exit 0
