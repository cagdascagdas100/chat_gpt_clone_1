param([switch]$Once)
$ErrorActionPreference = 'Continue'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { $PSScriptRoot }
$PollSeconds = if ($env:AAYS_RUNNER_POLL_SECONDS) { [int]$env:AAYS_RUNNER_POLL_SECONDS } else { 20 }
$DefaultTimeout = if ($env:AAYS_TASK_TIMEOUT_SECONDS) { [int]$env:AAYS_TASK_TIMEOUT_SECONDS } else { 1800 }
$QueueDir = Join-Path $BridgeRoot 'ai-queue'
$TaskFile = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$LastFile = Join-Path $BridgeRoot 'ai-tasks\.supervisor-v2-last-task-id'
$HeartbeatFile = Join-Path $BridgeRoot 'ai-heartbeat\autopilot-supervisor-v2.md'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ScriptDir = Join-Path $BridgeRoot 'ai-task-scripts'
New-Item -ItemType Directory -Force -Path $QueueDir,(Join-Path $BridgeRoot 'ai-tasks'),(Join-Path $BridgeRoot 'ai-heartbeat'),$LogDir,$ResultDir,$ScriptDir | Out-Null
$SupervisorLog = Join-Path $LogDir ('autopilot-supervisor-v2-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
function Log([string]$m){ $line='['+(Get-Date -Format s)+'] '+$m; Write-Output $line; Add-Content -Encoding UTF8 -Path $SupervisorLog -Value $line }
function HB([string]$status,[string]$taskId,[string]$msg){ @('# AAYS Autopilot Supervisor V2 Force Sync','',('Time: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),('Status: '+$status),('TaskId: '+$taskId),('BridgeRoot: '+$BridgeRoot),('TaskFile: '+$TaskFile),('QueueDir: '+$QueueDir),('SupervisorLog: '+$SupervisorLog),('Message: '+$msg),'Mode: force-sync-supervised-timeout-child-process','Reads: ai-queue first, then current-task script_path only') | Set-Content -Encoding UTF8 -Path $HeartbeatFile }
function Git([string[]]$args){ try{ Push-Location $BridgeRoot; $o=(& git @args 2>&1 | Out-String); Add-Content -Encoding UTF8 -Path $SupervisorLog -Value $o; return $o } catch { return $_.Exception.Message } finally { Pop-Location } }
function PushLocal(){ Git @('add','ai-results','ai-heartbeat','ai-tasks','ai-runner-logs') | Out-Null; $c=Git @('commit','-m',('Autopilot supervisor v2 snapshot '+(Get-Date -Format 'yyyyMMdd-HHmmss'))); Git @('pull','--rebase','origin','main') | Out-Null; Git @('push','origin','main') | Out-Null }
function ForceSync(){
  PushLocal | Out-Null
  Git @('fetch','origin','main') | Out-Null
  Git @('reset','--hard','origin/main') | Out-Null
  Git @('clean','-fd','--','ai-queue','ai-tasks','ai-task-scripts') | Out-Null
  Git @('pull','--ff-only','origin','main') | Out-Null
}
function ReadJson([string]$path){ try{ if(!(Test-Path $path)){ return $null }; $raw=Get-Content -Raw -Encoding UTF8 $path; if([string]::IsNullOrWhiteSpace($raw)){ return $null }; return ($raw | ConvertFrom-Json) } catch { Log ('JSON_ERROR '+$path+' '+$_.Exception.Message); return $null } }
function GetTask(){
  $q=Get-ChildItem $QueueDir -Filter '*.json' -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -First 1
  if($q){ $t=ReadJson $q.FullName; if($t){ $t | Add-Member -NotePropertyName _queue_file -NotePropertyValue $q.FullName -Force; return $t } }
  $t2=ReadJson $TaskFile
  if($t2 -and ($t2.PSObject.Properties.Name -contains 'script_path')){ return $t2 }
  return $null
}
function RunTask($task){
  $id=[string]$task.id
  if([string]::IsNullOrWhiteSpace($id)){ return }
  $last=if(Test-Path $LastFile){ (Get-Content -Raw -Encoding UTF8 $LastFile).Trim() } else { '' }
  if($id -eq $last){ HB 'polling' $id 'already-processed-or-waiting'; return }
  $candidate=if($task.PSObject.Properties.Name -contains 'script_path'){ [string]$task.script_path } else { '' }
  if([string]::IsNullOrWhiteSpace($candidate)){ HB 'rejected' $id 'missing script_path'; Set-Content -Encoding UTF8 -Path $LastFile -Value $id; PushLocal; return }
  if($candidate -match '\.\.'){ HB 'rejected' $id 'parent traversal blocked'; Set-Content -Encoding UTF8 -Path $LastFile -Value $id; PushLocal; return }
  $script=[IO.Path]::GetFullPath((Join-Path $ScriptDir $candidate)); $root=[IO.Path]::GetFullPath($ScriptDir)
  if(-not $script.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)){ HB 'rejected' $id 'outside script dir'; Set-Content -Encoding UTF8 -Path $LastFile -Value $id; PushLocal; return }
  if(!(Test-Path $script)){ HB 'rejected' $id ('script not found '+$script); Set-Content -Encoding UTF8 -Path $LastFile -Value $id; PushLocal; return }
  $timeout=if($task.PSObject.Properties.Name -contains 'timeout_seconds'){ [int]$task.timeout_seconds } else { $DefaultTimeout }
  $wd=if($task.PSObject.Properties.Name -contains 'working_directory'){ [string]$task.working_directory } else { $BridgeRoot }
  $out=Join-Path $LogDir ($id+'-v2-stdout.log'); $err=Join-Path $LogDir ($id+'-v2-stderr.log')
  HB 'running' $id ('script='+$candidate+' timeout='+$timeout)
  $p=Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$script) -WorkingDirectory $wd -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -WindowStyle Hidden
  $ok=$p.WaitForExit($timeout*1000)
  $exit=999
  if(-not $ok){ try{ Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }catch{}; $exit=124; HB 'timeout' $id ('timeout_seconds='+$timeout) } else { $exit=$p.ExitCode; HB 'finished' $id ('exit='+$exit) }
  $res=Join-Path $ResultDir ((Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')+'-'+$id+'-v2-result.md')
  @('# AAYS Autopilot Supervisor V2 Result','',('TaskId: '+$id),('ExitCode: '+$exit),('Time: '+(Get-Date -Format s)),'','## STDOUT','```text') | Set-Content -Encoding UTF8 -Path $res
  if(Test-Path $out){ Get-Content -Raw -Encoding UTF8 $out | Add-Content -Encoding UTF8 -Path $res }
  Add-Content -Encoding UTF8 -Path $res -Value '```'
  Add-Content -Encoding UTF8 -Path $res -Value @('','## STDERR','```text')
  if(Test-Path $err){ Get-Content -Raw -Encoding UTF8 $err | Add-Content -Encoding UTF8 -Path $res }
  Add-Content -Encoding UTF8 -Path $res -Value '```'
  Set-Content -Encoding UTF8 -Path $LastFile -Value $id
  if($task.PSObject.Properties.Name -contains '_queue_file'){ Move-Item -Force $task._queue_file ($task._queue_file+'.done') -ErrorAction SilentlyContinue }
  PushLocal
}
Log 'AAYS Autopilot Supervisor V2 Force Sync started.'
HB 'polling' '' 'started'
while($true){ try{ ForceSync; $task=GetTask; if($task){ RunTask $task } else { HB 'polling' '' 'no-script-task'; PushLocal } } catch { Log ('LOOP_ERROR '+$_.Exception.Message); HB 'error' '' $_.Exception.Message; PushLocal }; if($Once){ break }; Start-Sleep -Seconds $PollSeconds }
