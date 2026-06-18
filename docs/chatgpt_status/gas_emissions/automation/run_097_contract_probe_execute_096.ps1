$ErrorActionPreference='Stop'
$PageKey='gas_emissions'
$TaskId='terrayield-097-contract-probe-execute-096'
$Branch='feature/terrayield-aays-integration'
$ReportDir="docs/chatgpt_status/$PageKey/reports"
$StatusDir="docs/chatgpt_status/$PageKey/status"
$OutDir="docs/chatgpt_status/$PageKey/runner_outputs"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir,$OutDir | Out-Null
$Report=Join-Path $ReportDir "$TaskId.txt"
$StatusFile=Join-Path $StatusDir "$TaskId.txt"
$JsonOut=Join-Path $OutDir 'gas_emissions_097_contract_probe_execute_096_latest.json'
$FinalReport=Join-Path $ReportDir 'terrayield-093-gas-emissions-contract-runtime-finalize.txt'
$FinalJson=Join-Path $OutDir 'gas_emissions_093_final_contract_latest.json'
$Script096='docs/chatgpt_status/gas_emissions/automation/run_096_runtime_source_final.ps1'
function W($p,$a){$d=Split-Path -Parent $p;if($d){New-Item -ItemType Directory -Force $d|Out-Null};$a|Set-Content -Encoding UTF8 $p}
function Exists($p){return (Test-Path -LiteralPath $p)}
$probe=@('status=RUNNING','task_id='+$TaskId,'page_key='+$PageKey,'branch='+$Branch,'automation_path=docs/chatgpt_status/gas_emissions/automation/run_097_contract_probe_execute_096.ps1','delegates_to='+$Script096,'manual_stdout_required=false','fake_data=false','db_write=false','migration=false','production_deploy=false','started_at='+((Get-Date).ToString('o')))
foreach($p in @('docs/chatgpt_status/gas_emissions/current-task.txt','docs/chatgpt_status/gas_emissions/runner_tasks/096.task','docs/chatgpt_status/gas_emissions/queue/096.task','docs/chatgpt_status/gas_emissions/status/terrayield-096-runtime-source-final.path','docs/chatgpt_status/gas_emissions/control/096.contract.path',$Script096)){$probe += ('probe_'+($p -replace '[^A-Za-z0-9]','_')+'='+($(if(Exists $p){'exists'}else{'missing'})))}
W $Report $probe
W $StatusFile @('status=RUNNING','task_id='+$TaskId,'page_key='+$PageKey,'completion_percent=99','final_ready=false','report='+$Report,'delegates_to='+$Script096)
try{
 if(!(Exists $Script096)){throw 'missing delegated 096 automation'}
 $exe=$null
 foreach($c in @('powershell.exe','powershell','pwsh.exe','pwsh')){try{$cmd=Get-Command $c -ErrorAction Stop;$exe=$cmd.Source;break}catch{}}
 if(!$exe){throw 'no powershell executable available for child execution'}
 $abs=(Resolve-Path -LiteralPath $Script096).Path
 $proc=Start-Process -FilePath $exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$abs) -NoNewWindow -Wait -PassThru
 $exit=$proc.ExitCode
 $finalText='';if(Exists $FinalReport){$finalText=Get-Content -LiteralPath $FinalReport -Raw}
 $finalJsonText='';if(Exists $FinalJson){$finalJsonText=Get-Content -LiteralPath $FinalJson -Raw}
 $isReady=($finalText -match 'FINAL_READY' -and $finalText -match 'completion_percent=100' -and $finalText -match 'final_ready=true') -or ($finalJsonText -match '"final_ready"\s*:\s*true' -and $finalJsonText -match '"completion_percent"\s*:\s*100')
 $status= if($isReady){'FINAL_READY'} elseif($finalText -match 'status=FAILED' -or $finalJsonText -match '"status"\s*:\s*"FAILED"'){'DELEGATED_FAILED'} else {'DELEGATED_RAN_NOT_FINAL'}
 $pct= if($isReady){100}else{99}
 $rows=$probe + @('child_exit_code='+$exit,'delegated_status='+$status,'completion_percent='+$pct,'final_ready='+($isReady.ToString().ToLowerInvariant()),'final_report='+$FinalReport,'final_json='+$FinalJson)
 W $Report $rows
 @{task_id=$TaskId;page_key=$PageKey;status=$status;completion_percent=$pct;final_ready=$isReady;child_exit_code=$exit;final_report=$FinalReport;final_json=$FinalJson;delegates_to=$Script096;manual_stdout_required=$false;fake_data=$false}|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 $JsonOut
 W $StatusFile @('status='+$status,'task_id='+$TaskId,'page_key='+$PageKey,'completion_percent='+$pct,'final_ready='+($isReady.ToString().ToLowerInvariant()),'report='+$Report,'json_output='+$JsonOut,'delegates_to='+$Script096)
 git add $Report $StatusFile $JsonOut $FinalReport $FinalJson 2>$null;git commit -m 'terrayield 097 contract probe execute 096 report' 2>$null;git push origin $Branch 2>$null
 exit 0
}catch{
 $rows=$probe + @('status=FAILED','completion_percent=90','final_ready=false','error='+$_.Exception.Message)
 W $Report $rows
 @{task_id=$TaskId;page_key=$PageKey;status='FAILED';completion_percent=90;final_ready=$false;error=$_.Exception.Message;delegates_to=$Script096;manual_stdout_required=$false;fake_data=$false}|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 $JsonOut
 W $StatusFile @('status=FAILED','task_id='+$TaskId,'page_key='+$PageKey,'completion_percent=90','final_ready=false','error='+$_.Exception.Message,'report='+$Report)
 git add $Report $StatusFile $JsonOut 2>$null;git commit -m 'terrayield 097 contract probe failed report' 2>$null;git push origin $Branch 2>$null
 exit 0
}
