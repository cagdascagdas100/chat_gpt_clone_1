$TaskId='ty139-app-api-finalize'
$Bridge='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Out=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
Set-Location $Project
$targets=@('app\services\contractor_export_service.py','app\api\routes\contractor_exports.py','app\main.py')
$compile=(& python -m py_compile @targets 2>&1 | Out-String)
$compileExit=$LASTEXITCODE
$before=(git status --short -- $targets 2>&1 | Out-String)
$addOut=''
$saveOut=''
$syncOut=''
$sendOut=''
$progress=92
if($compileExit -eq 0){
  $addOut=(git add -- $targets 2>&1 | Out-String)
  $staged=(git diff --cached --name-only -- $targets 2>&1 | Out-String)
  if(-not [string]::IsNullOrWhiteSpace($staged)){
    $saveOut=(git commit -m 'feat contractors readonly export api' 2>&1 | Out-String)
  } else { $saveOut='No staged changes for target API files.' }
  $syncOut=(git pull --rebase --autostash origin main 2>&1 | Out-String)
  $sendOut=(git push origin main 2>&1 | Out-String)
  if($LASTEXITCODE -eq 0){$progress=96}else{$progress=94}
}else{
  $saveOut='Skipped because compile failed.'
}
$after=(git status --short -- $targets 2>&1 | Out-String)
$report=@('# TY139 App API Finalize','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('Compile exit code: '+$compileExit),'','## Target status before','```text',$before,'```','','## Add output','```text',$addOut,'```','','## Save output','```text',$saveOut,'```','','## Sync output','```text',$syncOut,'```','','## Send output','```text',$sendOut,'```','','## Target status after','```text',$after,'```','','## Next Action','Run final UI/dashboard wiring check and close integration.')
$report | Set-Content -Encoding UTF8 (Join-Path $Out 'ty139-app-api-finalize.report.md')
Write-Output ('PLAN_PROGRESS_PERCENT='+$progress)
Write-Output ('PLAN_PERCENT_REMAINING='+(100-$progress))
exit 0
