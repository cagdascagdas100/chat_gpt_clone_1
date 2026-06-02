$TaskId='ty139-commit-app-api-patch'
$Bridge='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Out=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
Set-Location $Project
$targets=@('app\services\contractor_export_service.py','app\api\routes\contractor_exports.py','app\main.py')
$compile=(& python -m py_compile @targets 2>&1 | Out-String)
$compileExit=$LASTEXITCODE
$before=(git status --short -- $targets 2>&1 | Out-String)
$commitOut=''
$pushOut=''
$progress=92
if($compileExit -eq 0){
  git add -- $targets | Out-Null
  $staged=(git diff --cached --name-only -- $targets 2>&1 | Out-String)
  if(-not [string]::IsNullOrWhiteSpace($staged)){
    $commitOut=(git commit -m 'feat(contractors): expose read-only contractor export API' 2>&1 | Out-String)
  } else { $commitOut='No staged API patch changes.' }
  $pullOut=(git pull --rebase --autostash origin main 2>&1 | Out-String)
  $pushOut=(git push origin main 2>&1 | Out-String)
  if($LASTEXITCODE -eq 0){$progress=96}else{$progress=94}
}else{$progress=92;$commitOut='Skipped commit because compile failed.'}
$after=(git status --short -- $targets 2>&1 | Out-String)
$report=@('# TY139 Commit App API Patch','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('Compile exit code: '+$compileExit),'','## Before status','```text',$before,'```','','## Commit output','```text',$commitOut,'```','','## Pull output','```text',$pullOut,'```','','## Push output','```text',$pushOut,'```','','## After status','```text',$after,'```','','## Next Action','Run final endpoint/dashboard wiring check.')
$report | Set-Content -Encoding UTF8 (Join-Path $Out 'ty139-commit-app-api-patch.report.md')
Write-Output ('PLAN_PROGRESS_PERCENT='+$progress)
Write-Output ('PLAN_PERCENT_REMAINING='+(100-$progress))
exit 0
