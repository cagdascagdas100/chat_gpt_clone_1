$ErrorActionPreference='Continue'
$TaskId='aays-041-psql-admin-install-retry-20260513'
$BridgeRoot=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir=Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir|Out-Null
function L($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function FindPsql{$cmd=Get-Command psql -ErrorAction SilentlyContinue;if($cmd){return $cmd.Source};$paths=@('C:\Program Files\PostgreSQL\17\bin\psql.exe','C:\Program Files\PostgreSQL\16\bin\psql.exe','C:\Program Files\PostgreSQL\15\bin\psql.exe','C:\Program Files\PostgreSQL\14\bin\psql.exe','C:\Program Files\PostgreSQL\13\bin\psql.exe','C:\Program Files\PostgreSQL\12\bin\psql.exe');foreach($p in $paths){if(Test-Path $p){return $p}};return $null}
L "TASK=$TaskId"
L 'MODE=psql_admin_install_retry'
L 'NO_DB_WRITE=true'
L 'NO_UI_PATCH=true'
$before=FindPsql
L ('PSQL_BEFORE='+$before)
$winget=Get-Command winget -ErrorAction SilentlyContinue
$attempted=$false;$exit=''
if(-not $before -and $winget){
  L 'WINGET_FOUND=true'
  try{winget install --id PostgreSQL.PostgreSQL -e --accept-source-agreements --accept-package-agreements;$exit=[string]$LASTEXITCODE;$attempted=$true;L ('WINGET_INTERACTIVE_EXIT_CODE='+$exit)}catch{L ('WINGET_INTERACTIVE_ERROR='+$_.Exception.Message)}
}else{if(-not $winget){L 'WINGET_FOUND=false'}}
Start-Sleep -Seconds 10
$after=FindPsql
$found=$false
if($after){$found=$true;$bin=Split-Path $after -Parent;if($env:Path -notlike ('*'+$bin+'*')){$env:Path=$bin+';'+$env:Path;L ('SESSION_PATH_ADDED='+$bin)};try{$up=[Environment]::GetEnvironmentVariable('Path','User');if($up -notlike ('*'+$bin+'*')){[Environment]::SetEnvironmentVariable('Path',($bin+';'+$up),'User');L ('USER_PATH_ADDED='+$bin)}}catch{L ('USER_PATH_ERROR='+$_.Exception.Message)};try{$ver=& $after --version 2>&1|Out-String;L ('PSQL_VERSION='+$ver.Trim())}catch{}}
$progress=if($found){82}else{72}
$manual='Open PowerShell as Administrator and run: winget install --id PostgreSQL.PostgreSQL -e --accept-source-agreements --accept-package-agreements'
$out=Join-Path $ResultDir ($TaskId+'.report.md')
@('# AAYS 041 psql admin install retry','',"Generated: $(Get-Date -Format s)",'','## Summary',"- psql before: $before","- winget attempted: $attempted","- winget exit code: $exit","- psql after: $after","- psql found: $found","- plan progress percent: $progress",'','## Manual fallback',$manual,'','## Next',$(if($found){'Proceed to DB staging import dry-run. Wait 3-5 minutes, then say: devam et'}else{'psql still missing. Run the manual fallback in an Administrator PowerShell, then say: devam et'}),'','AAYS_041_PSQL_ADMIN_INSTALL_RETRY_DONE=true')|Set-Content -Encoding UTF8 -Path $out
@('# AAYS Portable Task Runner Fixed','',"Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",'Status: finished',"TaskId: $TaskId","BridgeRoot: $BridgeRoot","TaskFile: $(Join-Path $BridgeRoot 'ai-tasks\current-task.json')","Message: exit=0 aays_041_psql_admin_retry_done progress=$progress",'Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled')|Set-Content -Encoding UTF8 (Join-Path $HeartbeatDir 'portable-runner.md')
L ('PLAN_PROGRESS_PERCENT='+$progress)
L 'AAYS_041_PSQL_ADMIN_INSTALL_RETRY_DONE=true'
exit 0
