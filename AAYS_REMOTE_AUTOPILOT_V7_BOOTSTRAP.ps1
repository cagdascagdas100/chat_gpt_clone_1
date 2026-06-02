$ErrorActionPreference='Continue'
$BridgeRoot='C:\AAYS_GITHUB_BRIDGE_CLEAN'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Agent=Join-Path $BridgeRoot 'AAYS_REMOTE_AUTOPILOT_V7.ps1'
$Watchdog=Join-Path $BridgeRoot 'AAYS_REMOTE_AUTOPILOT_V7_WATCHDOG.ps1'
$TaskName='AAYS_TerraYield_RemoteAutopilotV7'
$WatchdogTaskName='AAYS_TerraYield_RemoteAutopilotV7_Watchdog'
New-Item -ItemType Directory -Force -Path (Join-Path $BridgeRoot 'ai-tasks'),(Join-Path $BridgeRoot 'ai-task-scripts'),(Join-Path $BridgeRoot 'ai-results'),(Join-Path $BridgeRoot 'ai-heartbeat'),(Join-Path $BridgeRoot 'ai-runner-logs'),(Join-Path $BridgeRoot 'ai-runner-state') | Out-Null
function Step($m){$line='['+(Get-Date -Format s)+'] '+$m; Write-Host $line}
Step 'BOOTSTRAP_V7_START'
$agentText=@'
$ErrorActionPreference='Continue'
$BridgeRoot='C:\AAYS_GITHUB_BRIDGE_CLEAN'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$TaskFile=Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$ScriptsDir=Join-Path $BridgeRoot 'ai-task-scripts'
$ResultsDir=Join-Path $BridgeRoot 'ai-results'
$LogDir=Join-Path $BridgeRoot 'ai-runner-logs'
$StateDir=Join-Path $BridgeRoot 'ai-runner-state'
$HbFile=Join-Path $BridgeRoot 'ai-heartbeat\remote-autopilot-v7.md'
$LastFile=Join-Path $StateDir 'remote-autopilot-v7.last-task-id'
$RunLog=Join-Path $LogDir ('remote-autopilot-v7-'+(Get-Date -Format yyyyMMdd_HHmmss)+'.log')
New-Item -ItemType Directory -Force -Path $ScriptsDir,$ResultsDir,$LogDir,$StateDir,(Split-Path $HbFile) | Out-Null
function Log($m){$line='['+(Get-Date -Format s)+'] '+$m; Write-Output $line; Add-Content -Encoding UTF8 -Path $RunLog -Value $line}
function HB($status,$task,$msg){Set-Content -Encoding UTF8 -Path $HbFile -Value @('# TerraYield Remote Autopilot V7','',('status: '+$status),('task_id: '+$task),('checked_at: '+(Get-Date -Format s)),('bridge_root: '+$BridgeRoot),('project_root: '+$ProjectRoot),('runner_log: '+$RunLog),('message: '+$msg))}
function Git($a){try{Push-Location $BridgeRoot; $o=(& git @a 2>&1 | Out-String); Add-Content -Encoding UTF8 -Path $RunLog -Value $o; return $o}catch{ return ('GIT_ERROR='+$_.Exception.Message)}finally{Pop-Location}}
function PullLatest(){Git @('fetch','origin','main')|Out-Null; $r=Git @('rebase','origin/main'); if($r -match 'CONFLICT|fatal:|error:'){Git @('rebase','--abort')|Out-Null; Git @('reset','--hard','origin/main')|Out-Null}}
function PushState($task){Git @('add','ai-results','ai-heartbeat','ai-runner-state','ai-runner-logs')|Out-Null; Git @('commit','-m',('autopilot-v7 result '+$task))|Out-Null; Git @('fetch','origin','main')|Out-Null; $r=Git @('rebase','origin/main'); if($r -match 'CONFLICT|fatal:|error:'){Git @('rebase','--abort')|Out-Null; Git @('reset','--hard','origin/main')|Out-Null; Git @('add','ai-results','ai-heartbeat','ai-runner-state','ai-runner-logs')|Out-Null; Git @('commit','-m',('autopilot-v7 result '+$task+' recovery'))|Out-Null}; Git @('push','origin','main')|Out-Null}
function WriteResult($id,$title,$code,$out,$err,$msg){$f=Join-Path $ResultsDir ((Get-Date -Format yyyy-MM-dd_HH-mm-ss)+'-'+$id+'.md'); $so=if(Test-Path $out){Get-Content -Raw -Encoding UTF8 $out}else{''}; $se=if(Test-Path $err){Get-Content -Raw -Encoding UTF8 $err}else{''}; Set-Content -Encoding UTF8 -Path $f -Value @('# TerraYield Autopilot V7 Result','',('task_id: '+$id),('title: '+$title),('exit_code: '+$code),('message: '+$msg),('time: '+(Get-Date -Format s)),'','## Output','```text'); Add-Content -Encoding UTF8 -Path $f -Value $so; Add-Content -Encoding UTF8 -Path $f -Value '```'; Add-Content -Encoding UTF8 -Path $f -Value @('','## Error','```text'); Add-Content -Encoding UTF8 -Path $f -Value $se; Add-Content -Encoding UTF8 -Path $f -Value '```'}
function RunTask($t){$id=[string]$t.id; $title=if($t.PSObject.Properties.Name -contains 'title'){[string]$t.title}else{$id}; $sp=if($t.PSObject.Properties.Name -contains 'script_path'){[string]$t.script_path}else{''}; $timeout=if($t.PSObject.Properties.Name -contains 'timeout_seconds'){[int]$t.timeout_seconds}else{3600}; $out=Join-Path $LogDir ($id+'.stdout.log'); $err=Join-Path $LogDir ($id+'.stderr.log'); if([string]::IsNullOrWhiteSpace($sp)){Set-Content -Encoding UTF8 -Path $err -Value 'missing script_path'; WriteResult $id $title 2 $out $err 'rejected_missing_script_path'; Set-Content -Encoding UTF8 -Path $LastFile -Value $id; HB 'rejected' $id 'missing script_path'; PushState $id; return}; if($sp -match '\.\.'){throw 'unsafe script_path'}; $script=[IO.Path]::GetFullPath((Join-Path $ScriptsDir $sp)); $allowed=[IO.Path]::GetFullPath($ScriptsDir); if(-not $script.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'script outside allowed dir'}; if(-not (Test-Path $script)){throw ('script missing: '+$script)}; HB 'running' $id $title; Log ('START '+$id+' '+$script); $code=999; try{$p=Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$script) -WorkingDirectory $ProjectRoot -RedirectStandardOutput $out -RedirectStandardError $err -PassThru; if(-not $p.WaitForExit($timeout*1000)){Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; $code=124}else{$code=if($null -eq $p.ExitCode){0}else{[int]$p.ExitCode}}}catch{Add-Content -Encoding UTF8 -Path $err -Value $_.Exception.Message; $code=998}; WriteResult $id $title $code $out $err 'completed_by_v7'; Set-Content -Encoding UTF8 -Path $LastFile -Value $id; HB 'finished' $id ('exit='+$code); Log ('FINISH '+$id+' EXIT='+$code); PushState $id}
Log 'Autopilot V7 started'; HB 'polling' '' 'started'
while($true){try{PullLatest; if(-not(Test-Path $TaskFile)){HB 'polling' '' 'no task file'; Start-Sleep 20; continue}; $task=(Get-Content -Raw -Encoding UTF8 $TaskFile|ConvertFrom-Json); $id=[string]$task.id; $last=if(Test-Path $LastFile){(Get-Content -Raw -Encoding UTF8 $LastFile).Trim()}else{''}; if($id -and $id -ne $last){RunTask $task}else{HB 'polling' $id 'waiting'}}catch{Log ('LOOP_ERROR '+$_.Exception.Message); HB 'error' '' $_.Exception.Message}; Start-Sleep 20}
'@
Set-Content -Encoding UTF8 -Path $Agent -Value $agentText
$watchdogText=@'
$BridgeRoot='C:\AAYS_GITHUB_BRIDGE_CLEAN'
$Agent=Join-Path $BridgeRoot 'AAYS_REMOTE_AUTOPILOT_V7.ps1'
$Hb=Join-Path $BridgeRoot 'ai-heartbeat\remote-autopilot-v7-watchdog.md'
New-Item -ItemType Directory -Force -Path (Split-Path $Hb) | Out-Null
$p=@(Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match 'AAYS_REMOTE_AUTOPILOT_V7\.ps1'})
if($p.Count -lt 1 -and (Test-Path $Agent)){Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$Agent) -WorkingDirectory $BridgeRoot -WindowStyle Minimized}
Set-Content -Encoding UTF8 -Path $Hb -Value @('# V7 Watchdog','',('checked_at: '+(Get-Date -Format s)),('process_count: '+$p.Count))
'@
Set-Content -Encoding UTF8 -Path $Watchdog -Value $watchdogText
Step 'AGENT_AND_WATCHDOG_WRITTEN'
Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match 'AAYS_REMOTE_AUTOPILOT_V7\.ps1|AAYS_REMOTE_AUTOPILOT_V6\.ps1|AAYS_PORTABLE_TASK_RUNNER_FIXED\.ps1'} | ForEach-Object {Step ('STOP_OLD_PID='+$_.ProcessId); Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}
try{$a=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "'+$Agent+'"') -WorkingDirectory $BridgeRoot; $t=New-ScheduledTaskTrigger -AtLogOn; Register-ScheduledTask -TaskName $TaskName -Action $a -Trigger $t -Description 'TerraYield Remote Autopilot V7' -Force|Out-Null; Step ('TASK_REGISTERED='+$TaskName)}catch{Step ('TASK_REGISTER_ERROR='+$_.Exception.Message)}
try{$a2=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "'+$Watchdog+'"') -WorkingDirectory $BridgeRoot; $t2=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650); Register-ScheduledTask -TaskName $WatchdogTaskName -Action $a2 -Trigger $t2 -Description 'TerraYield Remote Autopilot V7 Watchdog' -Force|Out-Null; Step ('TASK_REGISTERED='+$WatchdogTaskName)}catch{Step ('WATCHDOG_REGISTER_ERROR='+$_.Exception.Message)}
Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$Agent) -WorkingDirectory $BridgeRoot -WindowStyle Minimized
Start-Sleep 8
$p=@(Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match 'AAYS_REMOTE_AUTOPILOT_V7\.ps1'})
Step ('V7_PROCESS_COUNT='+$p.Count)
Get-Content (Join-Path $BridgeRoot 'ai-heartbeat\remote-autopilot-v7.md') -ErrorAction SilentlyContinue
Step 'BOOTSTRAP_V7_DONE'
