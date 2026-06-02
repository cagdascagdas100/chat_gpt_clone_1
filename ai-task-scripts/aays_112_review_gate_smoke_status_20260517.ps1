$ErrorActionPreference='Continue'
$TaskId='aays-112-review-gate-smoke-status-20260517'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir=Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$AaysRoot='C:\Users\cagda\Documents\GitHub\AAYS'
$Target=Join-Path $AaysRoot 'terrayield_land_intelligence'
$Report=Join-Path $ResultDir ($TaskId+'.report.md')
$Json=Join-Path $ResultDir ($TaskId+'.result.json')
$Hb=Join-Path $HeartbeatDir 'review-gate-smoke-status.md'
function RunT($wd,$exe,$arg,$sec){
 try{
  $psi=New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName=$exe; $psi.Arguments=$arg; $psi.WorkingDirectory=$wd
  $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.UseShellExecute=$false
  $p=[System.Diagnostics.Process]::Start($psi)
  if(-not $p.WaitForExit($sec*1000)){try{$p.Kill()}catch{};return [ordered]@{exit_code=124;output='TIMEOUT'}}
  $o=$p.StandardOutput.ReadToEnd();$e=$p.StandardError.ReadToEnd();return [ordered]@{exit_code=$p.ExitCode;output=(($o,$e)-join "`n").Trim()}
 }catch{return [ordered]@{exit_code=999;output=$_.Exception.Message}}
}
function TryGet($url){
 try{
  $r=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
  return [ordered]@{ok=$true;status=[int]$r.StatusCode;body=[string]$r.Content}
 }catch{return [ordered]@{ok=$false;status=0;body=$_.Exception.Message}}
}
$steps=@();$blockers=@();$backend_live=$false;$gate_safe=$false;$ui_live=$false;$tests_known=$false
@('# AAYS 112 Review Gate Smoke Status','',"Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",'Status: running',"TaskId: $TaskId",'Mode: read-only smoke/status; no DB writes; no production deploy') | Set-Content -Encoding UTF8 $Hb
if(Test-Path $Target){
 $r=RunT $Target 'python' '-m compileall app -q' 180;$steps+=@([ordered]@{step='compile app';result=$r});if($r.exit_code -ne 0){$blockers+='compile app failed'}
 $tf=Join-Path $Target 'tests\test_review_status_api.py'
 if(Test-Path $tf){$r=RunT $Target 'python' '-m pytest -q tests/test_review_status_api.py' 240;$steps+=@([ordered]@{step='pytest review status api';result=$r});$tests_known=$true;if($r.exit_code -ne 0){$blockers+='review status api tests failed'}}else{$blockers+='test_review_status_api.py not found'}
}else{$blockers+='target folder not found'}
$g=TryGet 'http://127.0.0.1:8010/api/review/gates'
if($g.ok){$backend_live=$true;if($g.body -match 'NOT_READY_FOR_AUTO_ACCEPT'){$gate_safe=$true}else{$blockers+='review gates endpoint did not contain NOT_READY_FOR_AUTO_ACCEPT'}}else{$blockers+='backend not live on 127.0.0.1:8010'}
$u=TryGet 'http://127.0.0.1:8010/england_map_web/'
if($u.ok){$ui_live=$true}
$s=TryGet 'http://127.0.0.1:8010/api/review/status/by-listing/OTM-16748769'
$lines=@('# AAYS 112 Review Gate Smoke Status Result','',"Generated: $(Get-Date -Format s)",'Mode: read-only smoke/status; no DB writes; no UI patch; no scoring changes.','',"backend_live: $backend_live","ui_live: $ui_live","gate_safe_not_ready_for_auto_accept: $gate_safe","tests_known: $tests_known",'production_acceptance_gate_expected: NOT_READY_FOR_AUTO_ACCEPT','production_auto_accept: NO-GO','verified_promotion: NO-GO without evidence_checked=yes and verified polygon/source','','## Endpoint snapshots','### /api/review/gates','```text',($g.body.Substring(0,[Math]::Min(2000,$g.body.Length))),'```','### /api/review/status/by-listing/OTM-16748769','```text',($s.body.Substring(0,[Math]::Min(2000,$s.body.Length))),'```','','## Blockers')
if($blockers.Count -eq 0){$lines+='- none'}else{foreach($b in $blockers){$lines+='- '+$b}}
$lines+='';$lines+='## Steps'
foreach($st in $steps){$lines+='### '+$st.step;$lines+='exit_code='+$st.result.exit_code;$out=[string]$st.result.output;if($out.Length -gt 2500){$out=$out.Substring(0,2500)+'...TRUNCATED'};$lines+='```text';$lines+=$out;$lines+='```'}
$ready=($blockers.Count -eq 0 -and $gate_safe)
$lines+='';$lines+='review_gate_smoke_ready='+$ready;$lines+='AAYS_112_REVIEW_GATE_SMOKE_STATUS_DONE=true'
$lines | Set-Content -Encoding UTF8 $Report
([ordered]@{task_id=$TaskId;backend_live=$backend_live;ui_live=$ui_live;gate_safe=$gate_safe;ready=$ready;blockers=$blockers;report_path=$Report;generated_at=(Get-Date -Format s)}|ConvertTo-Json -Depth 6)|Set-Content -Encoding UTF8 $Json
@('# AAYS 112 Review Gate Smoke Status','',"Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",'Status: finished',"TaskId: $TaskId","Message: ready=$ready gate_safe=$gate_safe backend_live=$backend_live ui_live=$ui_live",'Mode: read-only smoke/status; no DB writes; no production deploy') | Set-Content -Encoding UTF8 $Hb
Write-Output 'AAYS_112_REVIEW_GATE_SMOKE_STATUS_DONE=true'
Write-Output ('READY='+$ready)
Write-Output ('REPORT='+$Report)
exit 0
