param([switch]$Once)
$ErrorActionPreference = 'Continue'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { $PSScriptRoot }
$QueueDir = Join-Path $BridgeRoot 'ai-queue'
$TaskFile = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$LastFile = Join-Path $BridgeRoot 'ai-tasks\.supervisor-last-task-id'
$HeartbeatFile = Join-Path $BridgeRoot 'ai-heartbeat\autopilot-supervisor.md'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ScriptDir = Join-Path $BridgeRoot 'ai-task-scripts'
$PollSeconds = if ($env:AAYS_RUNNER_POLL_SECONDS) { [int]$env:AAYS_RUNNER_POLL_SECONDS } else { 20 }
$DefaultTimeout = if ($env:AAYS_TASK_TIMEOUT_SECONDS) { [int]$env:AAYS_TASK_TIMEOUT_SECONDS } else { 1800 }
New-Item -ItemType Directory -Force -Path $QueueDir,(Join-Path $BridgeRoot 'ai-tasks'),(Join-Path $BridgeRoot 'ai-heartbeat'),$LogDir,$ResultDir,$ScriptDir | Out-Null
$SupervisorLog = Join-Path $LogDir ('autopilot-supervisor-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
function Log([string]$m){ $line='['+(Get-Date -Format s)+'] '+$m; Write-Output $line; Add-Content -Encoding UTF8 -Path $SupervisorLog -Value $line }
function HB([string]$status,[string]$taskId,[string]$msg){ @('# AAYS Autopilot Supervisor','',('Time: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),('Status: '+$status),('TaskId: '+$taskId),('BridgeRoot: '+$BridgeRoot),('TaskFile: '+$TaskFile),('QueueDir: '+$QueueDir),('SupervisorLog: '+$SupervisorLog),('Message: '+$msg),'Mode: supervised-timeout-child-process','Reads: ai-queue first, then current-task script_path only') | Set-Content -Encoding UTF8 -Path $HeartbeatFile }
function Git([string[]]$args){ try{ Push-Location $BridgeRoot; $o=(& git @args 2>&1 | Out-String); Add-Content -Encoding UTF8 -Path $SupervisorLog -Value $o; return $o } catch { return $_.Exception.Message } finally { Pop-Location } }
function Sync(){ Git @('fetch','origin','main') | Out-Null; Git @('pull','--ff-only','origin','main') | Out-Null }
function Push([string]$taskId){ Git @('add','ai-results','ai-heartbeat','ai-tasks','.','ai-runner-logs') | Out-Null; $c=Git @('commit','-m',('Autopilot supervisor result '+$taskId)); if($c -notmatch 'nothing to commit'){ Git @('pull','--rebase','origin','main') | Out-Null; Git @('push','origin','main') | Out-Null } }
function ReadJsonFile([string]$path){ try{ if(!(Test-Path $path)){ return $null }; $raw=Get-Content -Raw -Encoding UTF8 $path; if([string]::IsNullOrWhiteSpace($raw)){return $null}; return ($raw | ConvertFrom-Json) } catch { Log ('JSON_ERROR '+$path+' '+$_.Exception.Message); return $null } }
function GetNextTask(){
  $q = Get-ChildItem $QueueDir -Filter '*.json' -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -First 1
  if($q){ $t=ReadJsonFile $q.FullName; if($t){ $t | Add-Member -NotePropertyName _queue_file -NotePropertyValue $q.FullName -Force; return $t } }
  $t2=ReadJsonFile $TaskFile
  if($t2 -and ($t2.PSObject.Properties.Name -contains 'script_path')){ return $t2 }
  return $null
}
function RunTask($task){
  $id=[string]$task.id
  if([string]::IsNullOrWhiteSpace($id)){ return }
  $last=if(Test-Path $LastFile){(Get-Content -Raw -Encoding UTF8 $LastFile).Trim()}else{''}
  if($id -eq $last){ HB 'polling' $id 'already-processed-or-waiting'; return }
  $candidate=if($task.PSObject.Properties.Name -contains 'script_path'){[string]$task.script_path}else{''}
  if([string]::IsNullOrWhiteSpace($candidate)){ HB 'rejected' $id 'missing script_path'; Set-Content -Encoding UTF8 -Path $LastFile -Value $id; Push $id; return }
  if($candidate -match '\.\.'){ HB 'rejected' $id 'parent traversal blocked'; Set-Content -Encoding UTF8 -Path $LastFile -Value $id; Push $id; return }
  $script=[IO.Path]::GetFullPath((Join-Path $ScriptDir $candidate)); $root=[IO.Path]::GetFullPath($ScriptDir)
  if(-not $script.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)){ HB 'rejected' $id 'outside script dir'; Set-Content -Encoding UTF8 -Path $LastFile -Value $id; Push $id; return }
  if(!(Test-Path $script)){ HB 'rejected' $id ('script not found '+$script); Set-Content -Encoding UTF8 -Path $LastFile -Value $id; Push $id; return }
  $timeout=if($task.PSObject.Properties.Name -contains 'timeout_seconds'){[int]$task.timeout_seconds}else{$DefaultTimeout}
  $wd=if($task.PSObject.Properties.Name -contains 'working_directory'){[string]$task.working_directory}else{$BridgeRoot}
  $out=Join-Path $LogDir ($id+'-supervised-stdout.log'); $err=Join-Path $LogDir ($id+'-supervised-stderr.log')
  HB 'running' $id ('script='+$candidate+' timeout='+$timeout)
  Log ('START '+$id+' '+$script)
  $p=Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$script) -WorkingDirectory $wd -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -WindowStyle Hidden
  $ok=$p.WaitForExit($timeout*1000)
  $exit=999
  if(-not $ok){ try{ Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }catch{}; $exit=124; HB 'timeout' $id ('timeout_seconds='+$timeout) } else { $exit=$p.ExitCode; HB 'finished' $id ('exit='+$exit) }
  $result=Join-Path $ResultDir ((Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')+'-'+$id+'-supervisor-result.md')
  @('# AAYS Autopilot Supervisor Result','',('TaskId: '+$id),('ExitCode: '+$exit),('Time: '+(Get-Date -Format s)),'','## STDOUT','```text') | Set-Content -Encoding UTF8 -Path $result
  if(Test-Path $out){ Get-Content -Raw -Encoding UTF8 $out | Add-Content -Encoding UTF8 -Path $result }
  Add-Content -Encoding UTF8 -Path $result -Value '```'
  Add-Content -Encoding UTF8 -Path $result -Value @('','## STDERR','```text')
  if(Test-Path $err){ Get-Content -Raw -Encoding UTF8 $err | Add-Content -Encoding UTF8 -Path $result }
  Add-Content -Encoding UTF8 -Path $result -Value '```'
  Set-Content -Encoding UTF8 -Path $LastFile -Value $id
  if($task.PSObject.Properties.Name -contains '_queue_file'){ Move-Item -Force $task._queue_file ($task._queue_file+'.done') -ErrorAction SilentlyContinue }
  Push $id
}
Log 'AAYS Autopilot Supervisor started.'
HB 'polling' '' 'started'
while($true){ try{ Sync; $task=GetNextTask; if($task){ RunTask $task } else { HB 'polling' '' 'no-script-task' } } catch { Log ('LOOP_ERROR '+$_.Exception.Message); HB 'error' '' $_.Exception.Message }; if($Once){break}; Start-Sleep -Seconds $PollSeconds }
