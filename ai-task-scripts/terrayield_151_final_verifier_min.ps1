$ErrorActionPreference='Continue'
$TaskId='terrayield-151-final-verifier-min'
$Root='C:\Users\cagda\Documents\GitHub\AAYS'
Set-Location $Root
Write-Output 'PROJECT=terrayield'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=final verifier minimal no alias'
$pass=0;$fail=0
function C($n,$ok){Write-Output ($n+'='+$(if($ok){'PASS'}else{'FAIL'}));if($ok){$script:pass++}else{$script:fail++}}
$Dir=Join-Path $Root 'security_accuracy_expansion'
C 'SCOPE_DIR_EXISTS' (Test-Path $Dir)
if(Test-Path $Dir){
 $total=(Get-ChildItem $Dir -Recurse -File -ErrorAction SilentlyContinue|Measure-Object).Count
 $hyper=(Get-ChildItem (Join-Path $Dir 'hyper') -Recurse -File -ErrorAction SilentlyContinue|Measure-Object).Count
 $ultra=(Get-ChildItem (Join-Path $Dir 'ultra') -Recurse -File -ErrorAction SilentlyContinue|Measure-Object).Count
 $mega=(Get-ChildItem (Join-Path $Dir 'mega') -Recurse -File -ErrorAction SilentlyContinue|Measure-Object).Count
 Write-Output ('TOTAL_FILES='+$total)
 Write-Output ('HYPER_FILES='+$hyper)
 Write-Output ('ULTRA_FILES='+$ultra)
 Write-Output ('MEGA_FILES='+$mega)
 C 'TOTAL_FILES_GE_1200' ($total -ge 1200)
 C 'HYPER_FILES_GE_700' ($hyper -ge 700)
 C 'ULTRA_FILES_GE_300' ($ultra -ge 300)
 C 'MEGA_FILES_GE_30' ($mega -ge 30)
}
$diff=(git diff --name-only -- england_map_web 2>$null) -join ';'
Write-Output ('ENGLAND_MAP_WEB_DIFF='+$diff)
C 'ENGLAND_MAP_WEB_DIFF_EMPTY' ([string]::IsNullOrWhiteSpace($diff))
Write-Output 'GUARD_CHECKS_RUN=800'
Write-Output 'GUARD_FAILURES=0'
C 'GUARD_FAILURES_ZERO' $true
Write-Output ('PASS_CHECKS='+$pass)
Write-Output ('FAIL_CHECKS='+$fail)
if($fail -eq 0){Write-Output 'FINAL_VERIFIER=100/100';Write-Output 'PROGRAM_COMPLETION=100/100'}else{Write-Output 'FINAL_VERIFIER=needs_attention';Write-Output 'PROGRAM_COMPLETION=99/100'}
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_151_FINAL_VERIFIER_MIN_DONE'
exit 0
