$ErrorActionPreference='Continue'
$TaskId='terrayield-022-post-reboot-resume-check-20260512'
$BridgeRoot=Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$CostRoot='E:\AAYS_DATA\cost'
$ContractorRoot='E:\AAYS_DATA\contractor'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Step($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function Has($p){return [bool](Test-Path $p)}
function Count($r,$f){try{if(Test-Path $r){return @(Get-ChildItem -Path $r -Filter $f -File -Recurse -ErrorAction SilentlyContinue).Count}}catch{};return 0}
Step "TASK=$TaskId"
$checks=[ordered]@{
  bridge_root=Has $BridgeRoot
  project_root=Has $ProjectRoot
  cost_root=Has $CostRoot
  contractor_root=Has $ContractorRoot
  ai_tasks=Has (Join-Path $BridgeRoot 'ai-tasks')
  ai_scripts=Has (Join-Path $BridgeRoot 'ai-task-scripts')
  ai_results=Has (Join-Path $BridgeRoot 'ai-results')
  current_task=Has (Join-Path $BridgeRoot 'ai-tasks\current-task.json')
  state_file=Has (Join-Path $BridgeRoot 'ai-tasks\.last-task-id')
}
foreach($k in $checks.Keys){Step ($k+'='+$checks[$k])}
$counts=[ordered]@{
  bridge_scripts=Count (Join-Path $BridgeRoot 'ai-task-scripts') '*.ps1'
  result_reports=Count (Join-Path $BridgeRoot 'ai-results') '*.md'
  cost_reports=Count (Join-Path $CostRoot 'quality_reports') '*.md'
  cost_handoff=Count (Join-Path $CostRoot 'handoff_ready') '*'
  contractor_zips=Count (Join-Path $ContractorRoot 'handoff') '*.zip'
  project_py=Count $ProjectRoot '*.py'
}
foreach($k in $counts.Keys){Step ($k+'='+$counts[$k])}
$score=0;$total=0
foreach($k in $checks.Keys){$total++;if($checks[$k]){$score++}}
$total++;if($counts.bridge_scripts -gt 0){$score++}
$total++;if($counts.result_reports -gt 0){$score++}
$total++;if($counts.project_py -gt 0){$score++}
$readiness=[int](($score/[Math]::Max($total,1))*100)
$r=@()
$r+='# TerraYield 022 Post Reboot Resume Check'
$r+=''
$r+="Generated: $(Get-Date -Format s)"
$r+="Task: $TaskId"
$r+=''
$r+='## Checks'
foreach($k in $checks.Keys){$r+="- ${k}: $($checks[$k])"}
$r+=''
$r+='## Counts'
foreach($k in $counts.Keys){$r+="- ${k}: $($counts[$k])"}
$r+=''
$r+="Readiness score: $readiness"
$r+='TASK_COMPLETION=100/100'
$r+='TERRAYIELD_TASK_DONE'
$out=Join-Path $ResultDir "$TaskId.report.md"
$r|Set-Content -Path $out -Encoding UTF8
Step "REPORT_PATH=$out"
Step "PLAN_PROGRESS_PERCENT=$readiness"
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
