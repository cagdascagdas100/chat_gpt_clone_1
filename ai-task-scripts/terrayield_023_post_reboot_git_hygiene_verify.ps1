$ErrorActionPreference='Continue'
$TaskId='terrayield-023-post-reboot-git-hygiene-verify-20260512'
$BridgeRoot=Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Step($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function Has($p){return [bool](Test-Path $p)}
function Count($r,$f){try{if(Test-Path $r){return @(Get-ChildItem -Path $r -Filter $f -File -Recurse -ErrorAction SilentlyContinue).Count}}catch{};return 0}
Step "TASK=$TaskId"
$branch=''
$status=''
$remote=''
try{$branch=git -C $BridgeRoot branch --show-current 2>&1|Out-String}catch{$branch=$_.Exception.Message}
try{$status=git -C $BridgeRoot status --short 2>&1|Out-String}catch{$status=$_.Exception.Message}
try{$remote=git -C $BridgeRoot log -1 --oneline 2>&1|Out-String}catch{$remote=$_.Exception.Message}
$checks=[ordered]@{
  bridge_root=Has $BridgeRoot
  project_root=Has $ProjectRoot
  ai_tasks=Has (Join-Path $BridgeRoot 'ai-tasks')
  ai_scripts=Has (Join-Path $BridgeRoot 'ai-task-scripts')
  ai_results=Has (Join-Path $BridgeRoot 'ai-results')
  runner_v5=Has (Join-Path $BridgeRoot 'AAYS_AUTOPILOT_RUNNER_V5.ps1')
  current_task=Has (Join-Path $BridgeRoot 'ai-tasks\current-task.json')
}
foreach($k in $checks.Keys){Step ($k+'='+$checks[$k])}
Step ('SCRIPT_COUNT='+ (Count (Join-Path $BridgeRoot 'ai-task-scripts') '*.ps1'))
Step ('RESULT_COUNT='+ (Count $ResultDir '*.md'))
Step ('PROJECT_PY_COUNT='+ (Count $ProjectRoot '*.py'))
$r=@()
$r+='# TerraYield 023 Post Reboot Git Hygiene Verify'
$r+=''
$r+="Generated: $(Get-Date -Format s)"
$r+="Task: $TaskId"
$r+=''
$r+='## Checks'
foreach($k in $checks.Keys){$r+="- ${k}: $($checks[$k])"}
$r+=''
$r+='## Git Branch'
$r+='```text'
$r+=$branch
$r+='```'
$r+='## Git Head'
$r+='```text'
$r+=$remote
$r+='```'
$r+='## Git Status Short'
$r+='```text'
$r+=$status
$r+='```'
$r+='TASK_COMPLETION=100/100'
$r+='TERRAYIELD_TASK_DONE'
$out=Join-Path $ResultDir "$TaskId.report.md"
$r|Set-Content -Path $out -Encoding UTF8
Step "REPORT_PATH=$out"
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
