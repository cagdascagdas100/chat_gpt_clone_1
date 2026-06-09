$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$RepoUrl='https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$AaysRepo='C:\Users\cagda\Documents\GitHub\AAYS'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Results=Join-Path $Bridge 'ai-results'
$RunRoot=Join-Path $Results ('FG444_100_01_READONLY_AUDIT_' + $Stamp)
$Report=Join-Path $RunRoot ('FG444_100_01_READONLY_AUDIT_REPORT_' + $Stamp + '.txt')
$Stdout=Join-Path $RunRoot ('FG444_100_01_READONLY_AUDIT_STDOUT_' + $Stamp + '.txt')
$Stderr=Join-Path $RunRoot ('FG444_100_01_READONLY_AUDIT_STDERR_' + $Stamp + '.txt')
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
function L([string]$x){ $x | Tee-Object -FilePath $Report -Append }
L 'FG444_100_01_READONLY_AUDIT_RUN_START'
L "STARTED_AT=$(Get-Date -Format s)"
L "AAYS_REPO=$AaysRepo"
L "RUN_ROOT=$RunRoot"
L 'SAFETY_DB_WRITE=false'
L 'SAFETY_DDL=false'
L 'SAFETY_MIGRATION=false'
L 'SAFETY_PRODUCTION_PUBLISH=false'
$env:FG444_DB_WRITE='false'
$env:FG444_DDL='false'
$env:FG444_MIGRATION='false'
$env:FG444_PRODUCTION_PUBLISH='false'
$env:FG444_PLAN_MODE='true'
$zipPath=Join-Path $AaysRepo 'FG444_100_COMPLETION_CHATGPT_HANDOFF_20260608.zip'
$promptPath=Join-Path $AaysRepo 'FG444_100_COMPLETION_CHATGPT_MASTER_PROMPT_TR.txt'
$scriptPath=Join-Path $AaysRepo 'powershell\FG444_100_01_RUN_READONLY_AUDIT.ps1'
L "ZIP_EXISTS=$(Test-Path $zipPath) ZIP=$zipPath"
L "PROMPT_EXISTS=$(Test-Path $promptPath) PROMPT=$promptPath"
L "AUDIT_SCRIPT_EXISTS=$(Test-Path $scriptPath) AUDIT_SCRIPT=$scriptPath"
$exitCode=$null
if(Test-Path $scriptPath){
  Push-Location $AaysRepo
  try{
    powershell -NoProfile -ExecutionPolicy Bypass -File '.\powershell\FG444_100_01_RUN_READONLY_AUDIT.ps1' *> $Stdout
    $exitCode=$LASTEXITCODE
  } catch {
    $_ | Out-String | Set-Content -Encoding UTF8 $Stderr
    $exitCode=999
  }
  Pop-Location
}else{
  'MISSING_AUDIT_SCRIPT' | Set-Content -Encoding UTF8 $Stderr
  $exitCode=404
}
L "AUDIT_EXIT=$exitCode"
L "STDOUT=$Stdout"
L "STDERR=$Stderr"
$auditFiles=@()
if(Test-Path $AaysRepo){
  $auditFiles=@(Get-ChildItem $AaysRepo -Recurse -File -Filter 'FG444_READONLY_AUDIT_*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 10)
}
L "AUDIT_JSON_COUNT=$($auditFiles.Count)"
foreach($f in $auditFiles){
  L "AUDIT_JSON=$($f.FullName)"
  Copy-Item $f.FullName (Join-Path $RunRoot $f.Name) -Force
}
L "FINISHED_AT=$(Get-Date -Format s)"
$pushBase='F:\chatgpt\AAYS_WORK'
if(-not (Test-Path 'F:\')){ $pushBase=$env:TEMP }
$PushWork=Join-Path $pushBase ('fg444_100_readonly_audit_push_' + $Stamp)
New-Item -ItemType Directory -Force -Path $pushBase | Out-Null
git clone $RepoUrl $PushWork 2>&1 | Add-Content -Encoding UTF8 $Report
Push-Location $PushWork
git checkout -B fg444-100-readonly-audit-latest origin/main 2>&1 | Add-Content -Encoding UTF8 $Report
$Dest=Join-Path $PushWork 'docs\chatgpt_status\FG444_100_READONLY_AUDIT'
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Copy-Item (Join-Path $RunRoot '*') $Dest -Force -ErrorAction SilentlyContinue
$Latest=Join-Path $Dest 'FG444_100_READONLY_AUDIT_LATEST.txt'
@"
FG444_100_READONLY_AUDIT_LATEST
STATUS=$((if($exitCode -eq 0 -and $auditFiles.Count -gt 0){'AUDIT_JSON_READY'}elseif($exitCode -eq 0){'AUDIT_RAN_NO_JSON_FOUND'}else{'AUDIT_FAILED_OR_MISSING'}))
EXIT_CODE=$exitCode
AUDIT_JSON_COUNT=$($auditFiles.Count)
RUN_ROOT=$RunRoot
REPORT=$Report
STDOUT=$Stdout
STDERR=$Stderr
DB_WRITE=false
DDL=false
MIGRATION=false
PRODUCTION_PUBLISH=false
CREATED_AT=$(Get-Date -Format s)
"@ | Set-Content -Encoding UTF8 $Latest
git config user.email 'aays-runner@example.local'
git config user.name 'AAYS Runner'
git add docs/chatgpt_status/FG444_100_READONLY_AUDIT 2>&1 | Add-Content -Encoding UTF8 $Report
git commit -m 'Add FG444 100 readonly audit result' 2>&1 | Add-Content -Encoding UTF8 $Report
git push origin HEAD:refs/heads/fg444-100-readonly-audit-latest --force-with-lease 2>&1 | Add-Content -Encoding UTF8 $Report
Pop-Location
L 'FG444_100_01_READONLY_AUDIT_RUN_END'
exit 0
