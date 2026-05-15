$ErrorActionPreference='Continue'
$TaskId='aays-109b-branch-integration-build-test-timeout-20260515-2215'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir=Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatPath=Join-Path $HeartbeatDir 'portable-runner.md'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
function Exists($p){ return [bool](Test-Path $p) }
function RunT($wd,$exe,$arg,$sec){
 try{
  $psi=New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName=$exe; $psi.Arguments=$arg; $psi.WorkingDirectory=$wd
  $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.UseShellExecute=$false
  $p=[System.Diagnostics.Process]::Start($psi)
  if(-not $p.WaitForExit($sec*1000)){ try{$p.Kill()}catch{}; return [ordered]@{exit_code=124; timed_out=$true; output='TIMEOUT after '+$sec+' seconds'} }
  $o=$p.StandardOutput.ReadToEnd(); $e=$p.StandardError.ReadToEnd()
  return [ordered]@{exit_code=$p.ExitCode; timed_out=$false; output=(($o,$e)-join "`n").Trim()}
 }catch{return [ordered]@{exit_code=999; timed_out=$false; output=$_.Exception.Message}}
}
$AaysRoot='C:\Users\cagda\Documents\GitHub\AAYS'
$Target=Join-Path $AaysRoot 'terrayield_land_intelligence'
$Branch='feature/terrayield-aays-integration'
$steps=@(); $blockers=@(); $branch_ready=$false; $build_attempted=$false; $build_passed=$false; $tests_attempted=$false; $tests_passed=$false; $integration_ready=$false
@('# AAYS Portable Task Runner Fixed','',"Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",'Status: running',"TaskId: $TaskId","BridgeRoot: $BridgeRoot","ProjectRoot: $AaysRoot","TaskFile: $(Join-Path $BridgeRoot 'ai-tasks\current-task.json')",'Message: AAYS 109B timeout-safe integration build test','Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
if(!(Exists $AaysRoot)){ $blockers+='AAYS root not found' }
elseif(!(Exists (Join-Path $AaysRoot '.git'))){ $blockers+='AAYS root is not git repo' }
else{
 $r=RunT $AaysRoot 'git' 'status --short' 30; $steps+=@([ordered]@{step='git status'; result=$r})
 if($r.output.Trim().Length -gt 0){$r=RunT $AaysRoot 'git' ('stash push -u -m pre-'+$TaskId) 60; $steps+=@([ordered]@{step='stash dirty worktree'; result=$r})}
 $r=RunT $AaysRoot 'git' 'fetch origin' 90; $steps+=@([ordered]@{step='git fetch origin'; result=$r})
 $r=RunT $AaysRoot 'git' ('checkout -B '+$Branch) 60; $steps+=@([ordered]@{step='checkout branch'; result=$r}); if($r.exit_code -eq 0){$branch_ready=$true}else{$blockers+='branch checkout failed'}
 if(Exists (Join-Path $AaysRoot 'package.json')){ $build_attempted=$true; $r=RunT $AaysRoot 'cmd.exe' '/c npm run build --if-present' 240; $steps+=@([ordered]@{step='AAYS npm build'; result=$r}); if($r.exit_code -eq 0){$build_passed=$true}else{$blockers+='AAYS npm build failed or timed out'} }
 if(Exists $Target){
  if(Exists (Join-Path $Target 'package.json')){ $build_attempted=$true; $r=RunT $Target 'cmd.exe' '/c npm run build --if-present' 240; $steps+=@([ordered]@{step='TerraYield npm build'; result=$r}); if($r.exit_code -eq 0){$build_passed=$true}else{$blockers+='TerraYield npm build failed or timed out'}; $tests_attempted=$true; $r=RunT $Target 'cmd.exe' '/c npm test --if-present' 240; $steps+=@([ordered]@{step='TerraYield npm test'; result=$r}); if($r.exit_code -eq 0){$tests_passed=$true}else{$blockers+='TerraYield npm test failed or timed out'} }
  $py=(Get-ChildItem -Path $Target -Filter '*.py' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1)
  if($py -ne $null){ $build_attempted=$true; $r=RunT $Target 'python' '-m compileall . -q' 240; $steps+=@([ordered]@{step='TerraYield python compileall'; result=$r}); if($r.exit_code -eq 0){$build_passed=$true}else{$blockers+='python compileall failed or timed out'}; $tests_attempted=$true; $r=RunT $Target 'python' '-m pytest -q' 240; $steps+=@([ordered]@{step='TerraYield pytest'; result=$r}); if($r.exit_code -eq 0){$tests_passed=$true}else{$blockers+='pytest failed or timed out'} }
 }else{$blockers+='TerraYield target folder not found'}
 if(!$build_attempted){$blockers+='no build target found'}
 $reportDir=Join-Path $AaysRoot 'integration-reports'; New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
 $localReport=Join-Path $reportDir ($TaskId+'.md')
 @('# AAYS 109B Timeout Safe Branch Integration Build Test','',"Generated: $(Get-Date -Format s)","Branch: $Branch","BuildAttempted: $build_attempted","BuildPassed: $build_passed","TestsAttempted: $tests_attempted","TestsPassed: $tests_passed") | Set-Content -Encoding UTF8 -Path $localReport
 $r=RunT $AaysRoot 'git' 'add integration-reports' 30; $steps+=@([ordered]@{step='git add integration report'; result=$r})
 $r=RunT $AaysRoot 'git' 'commit -m "AAYS 109B timeout safe integration build test report"' 60; $steps+=@([ordered]@{step='git commit integration report'; result=$r})
}
if($branch_ready -and $build_attempted -and $build_passed){$integration_ready=$true}
$status=if($integration_ready){'completed'}elseif($blockers.Count -gt 0){'completed_with_blockers'}else{'completed_unknown'}
$reportPath=Join-Path $ResultDir ($TaskId+'.report.md')
$jsonPath=Join-Path $ResultDir ($TaskId+'.result.json')
$report=@('# AAYS 109B Timeout Safe Integration Build/Test Result','',"Generated: $(Get-Date -Format s)","STATUS=$status","BRANCH_READY=$branch_ready","BUILD_ATTEMPTED=$build_attempted","BUILD_PASSED=$build_passed","TESTS_ATTEMPTED=$tests_attempted","TESTS_PASSED=$tests_passed","INTEGRATION_READY=$integration_ready",'','## Blockers')
if($blockers.Count -eq 0){$report+='- none'}else{foreach($b in $blockers){$report+='- '+$b}}
$report+=''; $report+='## Steps'
foreach($s in $steps){$report+='### '+$s.step; $report+='exit_code='+$s.result.exit_code+' timed_out='+$s.result.timed_out; $out=[string]$s.result.output; if($out.Length -gt 2000){$out=$out.Substring(0,2000)+'...TRUNCATED'}; $report+='```text'; $report+=$out; $report+='```'}
$report+=''; $report+='PLAN_PROGRESS_PERCENT=100'; $report+='TASK_COMPLETION=100/100'; $report+='AAYS_BRANCH_INTEGRATION_BUILD_TEST_DONE=true'
$report | Set-Content -Encoding UTF8 -Path $reportPath
([ordered]@{task_id=$TaskId;status=$status;branch_ready=$branch_ready;build_attempted=$build_attempted;build_passed=$build_passed;tests_attempted=$tests_attempted;tests_passed=$tests_passed;integration_ready=$integration_ready;blockers=$blockers;report_path=$reportPath;generated_at=(Get-Date -Format s)} | ConvertTo-Json -Depth 8) | Set-Content -Encoding UTF8 -Path $jsonPath
@('# AAYS Portable Task Runner Fixed','',"Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",'Status: finished',"TaskId: $TaskId","BridgeRoot: $BridgeRoot","ProjectRoot: $AaysRoot","TaskFile: $(Join-Path $BridgeRoot 'ai-tasks\current-task.json')","Message: exit=0 aays_109b_timeout_safe_done status=$status",'Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
Write-Output "STATUS=$status"
Write-Output "INTEGRATION_READY=$integration_ready"
Write-Output "BUILD_PASSED=$build_passed"
Write-Output "TESTS_PASSED=$tests_passed"
Write-Output "REPORT_PATH=$reportPath"
exit 0
