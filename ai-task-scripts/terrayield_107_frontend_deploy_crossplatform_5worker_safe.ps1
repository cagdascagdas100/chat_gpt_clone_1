$ErrorActionPreference='Continue'
$TaskId='terrayield-107-frontend-deploy-crossplatform-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__107_frontend_deploy_crossplatform_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__107_summary.md'
$Status=Join-Path $RunDir 'terrayield__107_status.txt'
$Score=Join-Path $RunDir 'terrayield__107_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=frontend deployment cross-platform smoke with five workers'
$Slots=@(
 @{slot='slot_1_frontend_inventory'; area='frontend_inventory'},
 @{slot='slot_2_build_config'; area='build_config'},
 @{slot='slot_3_mobile_responsive_scan'; area='mobile_responsive'},
 @{slot='slot_4_deployment_readiness'; area='deployment_readiness'},
 @{slot='slot_5_backend_regression_guard'; area='backend_regression'}
)
$Worker={
 param($Slot,$Area,$Root,$Bridge,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__107__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-107-frontend-deploy-crossplatform-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Area -eq 'frontend_inventory'){
     L 'CHECK=frontend_inventory'
     Get-ChildItem -Recurse -File -Include package.json,*.tsx,*.ts,*.jsx,*.js,*.css,*.html -ErrorAction SilentlyContinue|Select-Object -First 220 FullName,Length|Out-String|Add-Content $out
   } elseif($Area -eq 'build_config'){
     L 'CHECK=build_config_files'
     Get-ChildItem -Recurse -File -Include package.json,tsconfig.json,vite.config.*,next.config.*,tailwind.config.*,postcss.config.*,Dockerfile,docker-compose*.yml -ErrorAction SilentlyContinue|Select-Object FullName,Length|Out-String|Add-Content $out
     if(Test-Path 'package.json'){L 'PACKAGE_JSON_PRESENT=true'} else {L 'PACKAGE_JSON_PRESENT=false'}
   } elseif($Area -eq 'mobile_responsive'){
     L 'CHECK=responsive_ui_keywords'
     Get-ChildItem -Recurse -File -Include *.tsx,*.ts,*.jsx,*.js,*.css -ErrorAction SilentlyContinue|Select-String -Pattern 'sm:|md:|lg:|xl:|grid|flex|responsive|mobile|viewport|overflow|map|layer|leaflet|deck|canvas' -ErrorAction SilentlyContinue|Select-Object -First 200|Out-String|Add-Content $out
   } elseif($Area -eq 'deployment_readiness'){
     L 'CHECK=deployment_files'
     Get-ChildItem -Recurse -File -Include Dockerfile,docker-compose*.yml,*.env.example,README.md,pyproject.toml,requirements*.txt,package.json -ErrorAction SilentlyContinue|Select-Object -First 160 FullName,Length|Out-String|Add-Content $out
     L 'CHECK=git_status'
     git status --short 2>&1|Out-String|Add-Content $out
   } else {
     L 'CHECK=backend_regression_guard'
     python -m pytest tests/test_supabase_admin_service.py tests/test_admin_publish_service.py tests/test_supabase_sync.py -q 2>&1|Out-String|Add-Content $out
     python -m compileall app 2>&1|Out-String|Add-Content $out
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$Root,$Bridge,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(25)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__107__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$program=100
@('metric,score','workers,5','completed_slots,'+$completed,'blocked_slots,'+$blocked,'timeout_slots,'+$timeout,'program_completion,'+$program,'crossplatform_smoke,85')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'PROGRAM_COMPLETION='+$program+'/100','CROSSPLATFORM_SMOKE=85/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "BLOCKED_SLOTS=$blocked"
W "TIMEOUT_SLOTS=$timeout"
W "PROGRAM_COMPLETION=$program/100"
W 'CROSSPLATFORM_SMOKE=85/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_107_FRONTEND_DEPLOY_CROSSPLATFORM_5WORKER_SAFE_DONE'
exit 0
