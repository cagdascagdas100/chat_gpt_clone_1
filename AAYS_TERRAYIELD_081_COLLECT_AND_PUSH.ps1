$ErrorActionPreference='Continue'
$BridgeRoot='C:\Users\cagda\Documents\chat_gpt_clone_1'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$TaskId='terrayield-081-fix-supabase-import-order-5worker-local'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir=Join-Path $BridgeRoot 'ai-heartbeat'
$LogDir=Join-Path $BridgeRoot 'ai-runner-logs'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir,$LogDir | Out-Null
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$RunLog=Join-Path $LogDir ('terrayield-081-collect-'+$Stamp+'.log')
$ResultFile=Join-Path $ResultDir ('Runner V4 result '+$TaskId+'.md')
function W($x){Write-Host $x;Add-Content -Encoding UTF8 -Path $RunLog -Value $x}
W "START collect $TaskId"
$LatestRun=Get-ChildItem -LiteralPath (Join-Path $ProjectRoot '.aays_real_runs') -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'terrayield__081_fix_supabase_import_order_5worker__*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Set-Content -Encoding UTF8 -Path $ResultFile -Value @('# Runner V4 result '+$TaskId,'','PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'TIME='+(Get-Date -Format 's'),'RUN_LOG='+$RunLog,'')
if($LatestRun){
  Add-Content -Encoding UTF8 -Path $ResultFile -Value ('LATEST_RUN_DIR='+$LatestRun.FullName)
  Add-Content -Encoding UTF8 -Path $ResultFile -Value ''
  foreach($f in Get-ChildItem -LiteralPath $LatestRun.FullName -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 60){
    Add-Content -Encoding UTF8 -Path $ResultFile -Value ('## '+$f.FullName)
    Add-Content -Encoding UTF8 -Path $ResultFile -Value '```text'
    Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue | Add-Content -Encoding UTF8 -Path $ResultFile
    Add-Content -Encoding UTF8 -Path $ResultFile -Value '```'
  }
}else{
  Add-Content -Encoding UTF8 -Path $ResultFile -Value 'LATEST_RUN_DIR=not_found'
}
Set-Content -Encoding UTF8 -Path (Join-Path $BridgeRoot 'ai-tasks\.last-task-id') -Value $TaskId
Set-Content -Encoding UTF8 -Path (Join-Path $HeartbeatDir 'runner-v4.md') -Value @('# AAYS ChatGPT Runner V4','','Time: '+(Get-Date -Format 'MM/dd/yyyy HH:mm:ss'),'Status: finished '+$TaskId+' exit=0','BridgeRoot: '+$BridgeRoot,'ProjectRoot: '+$ProjectRoot,'ResultFile: '+$ResultFile,'Mode: collect-and-push')
Set-Location $BridgeRoot
Remove-Item '.git\index.lock' -Force -ErrorAction SilentlyContinue
try{git pull --ff-only origin main 2>&1 | Tee-Object -FilePath $RunLog -Append | Out-Host}catch{}
git add ai-results ai-heartbeat ai-tasks/.last-task-id ai-runner-logs 2>&1 | Tee-Object -FilePath $RunLog -Append | Out-Host
git commit -m ('Runner V4 result '+$TaskId) 2>&1 | Tee-Object -FilePath $RunLog -Append | Out-Host
git pull --rebase origin main 2>&1 | Tee-Object -FilePath $RunLog -Append | Out-Host
git push origin main 2>&1 | Tee-Object -FilePath $RunLog -Append | Out-Host
W "DONE collect $TaskId"
