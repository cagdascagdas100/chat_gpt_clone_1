$ErrorActionPreference='Continue'
$RepoUrl='https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$WorkRoot='F:\chatgpt\AAYS_WORK\FG444_LONDON'
$Repo=Join-Path $WorkRoot 'repo'
$Logs=Join-Path $WorkRoot 'logs'
$Artifacts=Join-Path $WorkRoot 'artifacts'
$RunRoot=Join-Path $Artifacts ('FG444_LONDON_01_READONLY_AUDIT_' + $Stamp)
New-Item -ItemType Directory -Force -Path $WorkRoot,$Logs,$Artifacts,$RunRoot | Out-Null
$Report=Join-Path $RunRoot ('FG444_LONDON_READONLY_AUDIT_REPORT_' + $Stamp + '.txt')
$Stdout=Join-Path $RunRoot ('FG444_LONDON_READONLY_AUDIT_STDOUT_' + $Stamp + '.txt')
$Stderr=Join-Path $RunRoot ('FG444_LONDON_READONLY_AUDIT_STDERR_' + $Stamp + '.txt')
function L([string]$x){ $x | Tee-Object -FilePath $Report -Append }
L 'FG444_LONDON_01_READONLY_AUDIT_RUN_START'
L "STARTED_AT=$(Get-Date -Format s)"
L "WORK_ROOT=$WorkRoot"
L "REPO=$Repo"
L 'SCOPE=LONDON_ONLY'
L 'REGION=London'
L 'SAFETY_DB_WRITE=false'
L 'SAFETY_DDL=false'
L 'SAFETY_MIGRATION=false'
L 'SAFETY_PRODUCTION_PUBLISH=false'
L 'SAFETY_FAKE_DATA=false'
$env:FG444_SCOPE='LONDON_ONLY'
$env:FG444_REGION='London'
$env:FG444_WORK_ROOT=$WorkRoot
$env:FG444_DB_WRITE='false'
$env:FG444_DDL='false'
$env:FG444_MIGRATION='false'
$env:FG444_PRODUCTION_PUBLISH='false'
$env:FG444_FAKE_DATA='false'
$env:FG444_PLAN_MODE='true'
try{
  if(Test-Path (Join-Path $Repo '.git')){
    Push-Location $Repo
    git fetch origin 2>&1 | Add-Content -Encoding UTF8 $Report
    git checkout main 2>&1 | Add-Content -Encoding UTF8 $Report
    git pull --ff-only origin main 2>&1 | Add-Content -Encoding UTF8 $Report
    Pop-Location
  }else{
    git clone $RepoUrl $Repo 2>&1 | Add-Content -Encoding UTF8 $Report
  }
}catch{ $_ | Out-String | Add-Content -Encoding UTF8 $Report }
$scriptPath=Join-Path $Repo 'powershell\FG444_100_01_RUN_READONLY_AUDIT.ps1'
$zipPath=Join-Path $Repo 'FG444_100_COMPLETION_CHATGPT_HANDOFF_20260608.zip'
$promptPath=Join-Path $Repo 'FG444_100_COMPLETION_CHATGPT_MASTER_PROMPT_TR.txt'
L "ZIP_EXISTS=$(Test-Path $zipPath) ZIP=$zipPath"
L "PROMPT_EXISTS=$(Test-Path $promptPath) PROMPT=$promptPath"
L "AUDIT_SCRIPT_EXISTS=$(Test-Path $scriptPath) AUDIT_SCRIPT=$scriptPath"
$exitCode=0
if(Test-Path $scriptPath){
  Push-Location $Repo
  try{
    powershell -NoProfile -ExecutionPolicy Bypass -File '.\powershell\FG444_100_01_RUN_READONLY_AUDIT.ps1' *> $Stdout
    $exitCode=$LASTEXITCODE
  }catch{
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
if(Test-Path $Repo){
  $auditFiles=@(Get-ChildItem $Repo -Recurse -File -Filter 'FG444_READONLY_AUDIT_*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 10)
}
L "AUDIT_JSON_COUNT=$($auditFiles.Count)"
foreach($f in $auditFiles){ L "AUDIT_JSON=$($f.FullName)"; Copy-Item $f.FullName (Join-Path $RunRoot $f.Name) -Force }
$PushWork=Join-Path $WorkRoot ('push_' + $Stamp)
git clone $RepoUrl $PushWork 2>&1 | Add-Content -Encoding UTF8 $Report
Push-Location $PushWork
git checkout -B fg444-london-readonly-audit-latest origin/main 2>&1 | Add-Content -Encoding UTF8 $Report
$Dest=Join-Path $PushWork 'docs\chatgpt_status\FG444_LONDON_READONLY_AUDIT'
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Copy-Item (Join-Path $RunRoot '*') $Dest -Force -ErrorAction SilentlyContinue
$Latest=Join-Path $Dest 'FG444_LONDON_READONLY_AUDIT_LATEST.txt'
@"
FG444_LONDON_READONLY_AUDIT_LATEST
STATUS=$((if($exitCode -eq 0 -and $auditFiles.Count -gt 0){'AUDIT_JSON_READY'}elseif($exitCode -eq 0){'AUDIT_RAN_NO_JSON_FOUND'}else{'AUDIT_FAILED_OR_MISSING'}))
EXIT_CODE=$exitCode
AUDIT_JSON_COUNT=$($auditFiles.Count)
SCOPE=LONDON_ONLY
REGION=London
WORK_ROOT=$WorkRoot
RUN_ROOT=$RunRoot
REPORT=$Report
STDOUT=$Stdout
STDERR=$Stderr
DB_WRITE=false
DDL=false
MIGRATION=false
PRODUCTION_PUBLISH=false
FAKE_DATA=false
CREATED_AT=$(Get-Date -Format s)
"@ | Set-Content -Encoding UTF8 $Latest
git config user.email 'aays-runner@example.local'
git config user.name 'AAYS Runner'
git add docs/chatgpt_status/FG444_LONDON_READONLY_AUDIT 2>&1 | Add-Content -Encoding UTF8 $Report
git commit -m 'Add FG444 London readonly audit result' 2>&1 | Add-Content -Encoding UTF8 $Report
git push origin HEAD:refs/heads/fg444-london-readonly-audit-latest --force-with-lease 2>&1 | Add-Content -Encoding UTF8 $Report
Pop-Location
L 'FG444_LONDON_01_READONLY_AUDIT_RUN_END'
exit 0
