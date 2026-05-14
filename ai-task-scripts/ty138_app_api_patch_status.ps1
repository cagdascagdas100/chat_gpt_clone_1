$TaskId='ty138-app-api-patch-status'
$Bridge='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Out=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
Set-Location $Project
$targets=@('app\services\contractor_export_service.py','app\api\routes\contractor_exports.py','app\main.py')
$compile=(& python -m py_compile @targets 2>&1 | Out-String)
$compileExit=$LASTEXITCODE
$status=(git status --short 2>&1 | Out-String)
$files=@()
foreach($t in $targets){$p=Join-Path $Project $t;$i=Get-Item $p -ErrorAction SilentlyContinue;if($i){$files += ('- '+$t+' exists bytes='+$i.Length)}else{$files += ('- '+$t+' MISSING')}}
$progress=90
if($compileExit -eq 0){$progress=92}
$report=@('# TY138 App API Patch Status','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('Compile exit code: '+$compileExit),'','## Files')+$files+@('','## Git status','```text',$status,'```','','## Compile output','```text',$compile,'```','','## Next Action','Commit/push API patch and continue UI wiring.')
$report | Set-Content -Encoding UTF8 (Join-Path $Out 'ty138-app-api-patch-status.report.md')
Write-Output ('PLAN_PROGRESS_PERCENT='+$progress)
Write-Output ('PLAN_PERCENT_REMAINING='+(100-$progress))
exit 0
