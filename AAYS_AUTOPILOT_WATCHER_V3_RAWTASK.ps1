param([switch]$Once)
$ErrorActionPreference = 'Continue'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { $PSScriptRoot }
$RepoRef = if ($env:AAYS_REPO_REF) { $env:AAYS_REPO_REF } else { 'origin/main' }
$PollSeconds = if ($env:AAYS_RUNNER_POLL_SECONDS) { [int]$env:AAYS_RUNNER_POLL_SECONDS } else { 20 }
$DefaultTimeout = if ($env:AAYS_TASK_TIMEOUT_SECONDS) { [int]$env:AAYS_TASK_TIMEOUT_SECONDS } else { 1800 }
$TaskPath = 'ai-tasks/current-task.json'
$HeartbeatFile = Join-Path $BridgeRoot 'ai-heartbeat\autopilot-watcher-v3.md'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$CacheDir = Join-Path $BridgeRoot 'ai-script-cache'
$LastFile = Join-Path $BridgeRoot 'ai-tasks\.watcher-v3-last-task-id'
New-Item -ItemType Directory -Force -Path (Join-Path $BridgeRoot 'ai-heartbeat'),$LogDir,$ResultDir,$CacheDir,(Join-Path $BridgeRoot 'ai-tasks') | Out-Null
$WatcherLog = Join-Path $LogDir ('autopilot-watcher-v3-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
function Log([string]$m){ $line='['+(Get-Date -Format s)+'] '+$m; Write-Output $line; Add-Content -Encoding UTF8 -Path $WatcherLog -Value $line }
function HB([string]$status,[string]$taskId,[string]$msg){ @('# AAYS Autopilot Watcher V3 RawTask','',('Time: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),('Status: '+$status),('TaskId: '+$taskId),('BridgeRoot: '+$BridgeRoot),('TaskSource: git show '+$RepoRef+':'+$TaskPath),('WatcherLog: '+$WatcherLog),('Message: '+$msg),'Mode: fetch-show-no-working-tree-reset','Reads: remote current-task via git show; downloads script via git show; child process with timeout') | Set-Content -Encoding UTF8 -Path $HeartbeatFile }
function Git([string[]]$args){ try{ Push-Location $BridgeRoot; $o=(& git @args 2>&1 | Out-String); Add-Content -Encoding UTF8 -Path $WatcherLog -Value $o; return $o } catch { return $_.Exception.Message } finally { try{Pop-Location}catch{} } }
function PushResults([string]$taskId){ try{ Push-Location $BridgeRoot; git add ai-results ai-heartbeat ai-tasks/.watcher-v3-last-task-id ai-runner-logs ai-script-cache 2>&1 | Out-String | Add-Content -Encoding UTF8 $WatcherLog; $c=(git commit -m "Watcher V3 result $taskId" 2>&1 | Out-String); Add-Content -Encoding UTF8 -Path $WatcherLog -Value $c; if($c -notmatch 'nothing to commit'){ git pull --rebase origin main 2>&1 | Out-String | Add-Content -Encoding UTF8 $WatcherLog; git push origin main 2>&1 | Out-String | Add-Content -Encoding UTF8 $WatcherLog } } catch { Add-Content -Encoding UTF8 -Path $WatcherLog -Value ('PUSH_ERROR '+$_.Exception.Message) } finally { try{Pop-Location}catch{} } }
function RemoteText([string]$path){ Git @('fetch','origin','main') | Out-Null; $txt=Git @('show',($RepoRef+':'+$path)); if($txt -match 'fatal:'){ return $null }; return $txt }
function ReadRemoteTask(){ try{ $raw=RemoteText $TaskPath; if([string]::IsNullOrWhiteSpace($raw)){ return $null }; return ($raw | ConvertFrom-Json) } catch { Log ('TASK_READ_ERROR '+$_.Exception.Message); return $null } }
function SaveRemoteScript([string]$scriptPath){ if([string]::IsNullOrWhiteSpace($scriptPath)){ return $null }; if($scriptPath -match '\.\.'){ return $null }; $remotePath='ai-task-scripts/'+$scriptPath; $txt=RemoteText $remotePath; if([string]::IsNullOrWhiteSpace($txt)){ return $null }; if($txt -match '^fatal:'){ return $null }; $local=Join-Path $CacheDir $scriptPath; Set-Content -Encoding UTF8 -Path $local -Value $txt; return $local }
function RunTask($task){
  $id=[string]$task.id
  if([string]::IsNullOrWhiteSpace($id)){ HB 'polling' '' 'remote task missing id'; return }
  $last=if(Test-Path $LastFile){ (Get-Content -Raw -Encoding UTF8 $LastFile).Trim() } else { '' }
  if($id -eq $last){ HB 'polling' $id 'already-processed-or-waiting'; return }
  $scriptName=if($task.PSObject.Properties.Name -contains 'script_path'){ [string]$task.script_path } else { '' }
  if([string]::IsNullOrWhiteSpace($scriptName)){ HB 'rejected' $id 'missing script_path'; Set-Content -Encoding UTF8 -Path $LastFile -Value $id; PushResults $id; return }
  $localScript=SaveRemoteScript $scriptName
  if(-not $localScript -or !(Test-Path $localScript)){ HB 'rejected' $id ('could not fetch script '+$scriptName); Set-Content -Encoding UTF8 -Path $LastFile -Value $id; PushResults $id; return }
  $timeout=if($task.PSObject.Properties.Name -contains 'timeout_seconds'){ [int]$task.timeout_seconds } else { $DefaultTimeout }
  $wd=if($task.PSObject.Properties.Name -contains 'working_directory'){ [string]$task.working_directory } else { $BridgeRoot }
  if(!(Test-Path $wd)){ $wd=$BridgeRoot }
  $out=Join-Path $LogDir ($id+'-v3-stdout.log'); $err=Join-Path $LogDir ($id+'-v3-stderr.log')
  HB 'running' $id ('script='+$scriptName+' timeout='+$timeout)
  Log ('START '+$id+' '+$localScript)
  $p=Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$localScript) -WorkingDirectory $wd -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -WindowStyle Hidden
  $ok=$p.WaitForExit($timeout*1000)
  $exit=999
  if(-not $ok){ try{ Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }catch{}; $exit=124; HB 'timeout' $id ('timeout_seconds='+$timeout) } else { $exit=$p.ExitCode; HB 'finished' $id ('exit='+$exit) }
  $res=Join-Path $ResultDir ((Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')+'-'+$id+'-v3-result.md')
  @('# AAYS Autopilot Watcher V3 Result','',('TaskId: '+$id),('Script: '+$scriptName),('ExitCode: '+$exit),('Time: '+(Get-Date -Format s)),'','## STDOUT','```text') | Set-Content -Encoding UTF8 -Path $res
  if(Test-Path $out){ Get-Content -Raw -Encoding UTF8 $out | Add-Content -Encoding UTF8 -Path $res }
  Add-Content -Encoding UTF8 -Path $res -Value '```'
  Add-Content -Encoding UTF8 -Path $res -Value @('','## STDERR','```text')
  if(Test-Path $err){ Get-Content -Raw -Encoding UTF8 $err | Add-Content -Encoding UTF8 -Path $res }
  Add-Content -Encoding UTF8 -Path $res -Value '```'
  Set-Content -Encoding UTF8 -Path $LastFile -Value $id
  PushResults $id
}
Log 'AAYS Autopilot Watcher V3 RawTask started.'
HB 'polling' '' 'started'
while($true){ try{ $task=ReadRemoteTask; if($task){ RunTask $task } else { HB 'polling' '' 'no-remote-script-task' } } catch { Log ('LOOP_ERROR '+$_.Exception.Message); HB 'error' '' $_.Exception.Message }; if($Once){ break }; Start-Sleep -Seconds $PollSeconds }
