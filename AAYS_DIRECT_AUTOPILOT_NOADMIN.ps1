$ErrorActionPreference = 'Continue'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\AAYS_GITHUB_BRIDGE_CLEAN2' }
$PollSeconds = if ($env:AAYS_RUNNER_POLL_SECONDS) { [int]$env:AAYS_RUNNER_POLL_SECONDS } else { 20 }
$DefaultTimeout = if ($env:AAYS_TASK_TIMEOUT_SECONDS) { [int]$env:AAYS_TASK_TIMEOUT_SECONDS } else { 1800 }
$TaskFile = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$LastFile = Join-Path $BridgeRoot 'ai-tasks\.direct-autopilot-last-task-id'
$HeartbeatFile = Join-Path $BridgeRoot 'ai-heartbeat\direct-autopilot.md'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ScriptDir = Join-Path $BridgeRoot 'ai-task-scripts'
New-Item -ItemType Directory -Force -Path (Join-Path $BridgeRoot 'ai-tasks'),(Join-Path $BridgeRoot 'ai-heartbeat'),$LogDir,$ResultDir,$ScriptDir | Out-Null
$MainLog = Join-Path $LogDir ('direct-autopilot-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
function Write-Log([string]$Message){ $line='['+(Get-Date -Format s)+'] '+$Message; $line | Tee-Object -FilePath $MainLog -Append }
function Write-Heartbeat([string]$Status,[string]$TaskId,[string]$Message){ @('# AAYS Direct Autopilot NoAdmin','',('Time: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),('Status: '+$Status),('TaskId: '+$TaskId),('BridgeRoot: '+$BridgeRoot),('TaskFile: '+$TaskFile),('MainLog: '+$MainLog),('Message: '+$Message),'Mode: direct-local-read-after-git-reset',('PollSeconds: '+$PollSeconds)) | Set-Content -Encoding UTF8 $HeartbeatFile }
function Invoke-Git([string[]]$GitArgs){ try{ Push-Location $BridgeRoot; $out=(& git @GitArgs 2>&1 | Out-String); Add-Content -Encoding UTF8 -Path $MainLog -Value ('> git '+($GitArgs -join ' ')); Add-Content -Encoding UTF8 -Path $MainLog -Value $out; return $out } catch { return $_.Exception.Message } finally { try{ Pop-Location }catch{} } }
function Sync-Repo(){ Invoke-Git -GitArgs @('fetch','origin','main') | Out-Null; Invoke-Git -GitArgs @('reset','--hard','origin/main') | Out-Null }
function Read-CurrentTask(){ try{ if(!(Test-Path $TaskFile)){ return $null }; $raw=Get-Content -Raw -Encoding UTF8 $TaskFile; if([string]::IsNullOrWhiteSpace($raw)){ return $null }; $raw=$raw -replace [char]0xFEFF,''; $first=$raw.IndexOf('{'); $last=$raw.LastIndexOf('}'); if($first -lt 0 -or $last -le $first){ return $null }; $json=$raw.Substring($first,$last-$first+1); return ($json | ConvertFrom-Json) } catch { Write-Log ('TASK_READ_ERROR: '+$_.Exception.Message); return $null } }
function Push-Results([string]$TaskId){ Invoke-Git -GitArgs @('add','ai-results','ai-heartbeat','ai-tasks\.direct-autopilot-last-task-id','ai-runner-logs') | Out-Null; $commit=Invoke-Git -GitArgs @('commit','-m',('Direct autopilot result '+$TaskId)); if($commit -match 'nothing to commit'){ return }; Invoke-Git -GitArgs @('pull','--rebase','origin','main') | Out-Null; Invoke-Git -GitArgs @('push','origin','main') | Out-Null }
function Run-Task($Task){
  if($null -eq $Task){ Write-Heartbeat 'polling' '' 'no-valid-task'; return }
  $TaskId=[string]$Task.id
  if([string]::IsNullOrWhiteSpace($TaskId)){ Write-Heartbeat 'polling' '' 'task-missing-id'; return }
  $ScriptName=''
  if($Task.PSObject.Properties.Name -contains 'script_path'){ $ScriptName=[string]$Task.script_path }
  if([string]::IsNullOrWhiteSpace($ScriptName)){ Write-Heartbeat 'rejected' $TaskId 'missing-script_path'; Set-Content -Encoding UTF8 -Path $LastFile -Value $TaskId; Push-Results $TaskId; return }
  $LastId=''
  if(Test-Path $LastFile){ $LastId=(Get-Content -Raw -Encoding UTF8 $LastFile).Trim() }
  if($TaskId -eq $LastId){ Write-Heartbeat 'polling' $TaskId 'already-processed-or-waiting'; return }
  if($ScriptName -match '\.\.'){ Write-Heartbeat 'rejected' $TaskId 'blocked-parent-traversal'; Set-Content -Encoding UTF8 -Path $LastFile -Value $TaskId; Push-Results $TaskId; return }
  $ScriptPath=Join-Path $ScriptDir $ScriptName
  if(!(Test-Path $ScriptPath)){ Write-Heartbeat 'rejected' $TaskId ('script-not-found: '+$ScriptPath); Set-Content -Encoding UTF8 -Path $LastFile -Value $TaskId; Push-Results $TaskId; return }
  $Timeout=$DefaultTimeout
  if($Task.PSObject.Properties.Name -contains 'timeout_seconds'){ $Timeout=[int]$Task.timeout_seconds }
  $WorkingDirectory=$BridgeRoot
  if($Task.PSObject.Properties.Name -contains 'working_directory'){ $WorkingDirectory=[string]$Task.working_directory }
  if(!(Test-Path $WorkingDirectory)){ $WorkingDirectory=$BridgeRoot }
  $Stdout=Join-Path $LogDir ($TaskId+'-direct-stdout.log')
  $Stderr=Join-Path $LogDir ($TaskId+'-direct-stderr.log')
  Write-Heartbeat 'running' $TaskId ('script='+$ScriptName+' timeout='+$Timeout)
  Write-Log ('START '+$TaskId+' '+$ScriptPath)
  $proc=Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$ScriptPath) -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru -WindowStyle Hidden
  $ok=$proc.WaitForExit($Timeout*1000)
  $ExitCode=999
  if(-not $ok){ try{ Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }catch{}; $ExitCode=124; Write-Heartbeat 'timeout' $TaskId ('timeout_seconds='+$Timeout) } else { $ExitCode=$proc.ExitCode; Write-Heartbeat 'finished' $TaskId ('exit='+$ExitCode) }
  $ResultPath=Join-Path $ResultDir ((Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')+'-'+$TaskId+'-direct-result.md')
  @('# AAYS Direct Autopilot Result','',('TaskId: '+$TaskId),('Script: '+$ScriptName),('ExitCode: '+$ExitCode),('Time: '+(Get-Date -Format s)),'','## STDOUT','```text') | Set-Content -Encoding UTF8 $ResultPath
  if(Test-Path $Stdout){ Get-Content -Raw -Encoding UTF8 $Stdout | Add-Content -Encoding UTF8 $ResultPath }
  Add-Content -Encoding UTF8 $ResultPath '```'
  Add-Content -Encoding UTF8 $ResultPath ''
  Add-Content -Encoding UTF8 $ResultPath '## STDERR'
  Add-Content -Encoding UTF8 $ResultPath '```text'
  if(Test-Path $Stderr){ Get-Content -Raw -Encoding UTF8 $Stderr | Add-Content -Encoding UTF8 $ResultPath }
  Add-Content -Encoding UTF8 $ResultPath '```'
  Set-Content -Encoding UTF8 -Path $LastFile -Value $TaskId
  Push-Results $TaskId
}
Write-Log 'AAYS Direct Autopilot started.'
Write-Heartbeat 'polling' '' 'started'
while($true){ try{ Sync-Repo; $task=Read-CurrentTask; Run-Task $task } catch { Write-Log ('LOOP_ERROR: '+$_.Exception.Message); Write-Heartbeat 'error' '' $_.Exception.Message }; Start-Sleep -Seconds $PollSeconds }
