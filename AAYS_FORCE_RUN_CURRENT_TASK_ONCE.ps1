$ErrorActionPreference='Continue'
$BridgeRoot='C:\Users\cagda\Documents\chat_gpt_clone_1'
$TaskFile=Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir=Join-Path $BridgeRoot 'ai-heartbeat'
$StateFile=Join-Path $BridgeRoot 'ai-tasks\.last-task-id'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir,(Split-Path $StateFile -Parent)|Out-Null
function WriteBeat($s){@('# AAYS Force Run Current Task Once','Time: '+(Get-Date),'Status: '+$s)|Set-Content -Encoding UTF8 (Join-Path $HeartbeatDir 'force-run-current-task-once.md')}
WriteBeat 'starting'
Set-Location $BridgeRoot
try{git pull --ff-only origin main|Out-Null}catch{}
if(!(Test-Path $TaskFile)){WriteBeat 'no-task-file'; exit 2}
$task=Get-Content -Raw -Encoding UTF8 $TaskFile|ConvertFrom-Json
$id=[string]$task.id
$wd=[string]$task.working_directory
$cmd=[string]$task.command
if([string]::IsNullOrWhiteSpace($id)){WriteBeat 'no-task-id'; exit 3}
if([string]::IsNullOrWhiteSpace($wd)){$wd='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'}
if([string]::IsNullOrWhiteSpace($cmd)){WriteBeat 'no-command'; exit 4}
WriteBeat ('running '+$id)
$stamp=Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$safe=$id -replace '[^a-zA-Z0-9_-]+','-'
$result=Join-Path $ResultDir ($stamp+'-'+$safe+'-force-run.md')
$old=Get-Location
try{
 Set-Location $wd
 $out=Invoke-Expression ($cmd+' 2>&1')|Out-String
 $exit=$LASTEXITCODE
 if($null -eq $exit){$exit=0}
}catch{
 $out=$_.Exception.Message
 $exit=900
}finally{Set-Location $old}
@('# AAYS Force Run Result','','Task ID: '+$id,'Time: '+(Get-Date),'ExitCode: '+$exit,'','```text',$out,'```')|Set-Content -Encoding UTF8 $result
$id|Set-Content -Encoding UTF8 $StateFile
WriteBeat ('finished '+$id+' exit='+$exit)
try{
 Set-Location $BridgeRoot
 git add ai-results ai-heartbeat ai-tasks|Out-Null
 git commit -m ('Force run current task result '+$id)|Out-Null
 git push|Out-Null
}catch{}
Write-Output ('FORCE_RUN_DONE '+$id+' exit='+$exit)
Write-Output ('RESULT_FILE='+$result)
exit $exit
