$ErrorActionPreference='Continue'
$TaskId='5-1-real-100-parallel-discovery-20260524'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Estate='E:\AAYS_DATA\estate_agents'
$Roots=@('E:\AAYS_DATA','C:\AAYS_GITHUB_BRIDGE_CLEAN2','C:\Users\cagda\Documents\GitHub\AAYS')
$Result=Join-Path $Bridge 'ai-results'
$Hb=Join-Path $Bridge 'ai-heartbeat\5_1_real_100_parallel_discovery.md'
New-Item -ItemType Directory -Force -Path $Estate,$Result,(Split-Path $Hb -Parent) | Out-Null
function Beat($m){@('# 5.1 Real 100 Parallel Discovery','status=running',('task_id='+$TaskId),('message='+$m),('time='+(Get-Date -Format s)),'db_write=false','production_deploy=false','fake_data=false')|Set-Content -Encoding UTF8 $Hb}
function SafeCountRows($p){try{if(Test-Path $p){return [Math]::Max(0,(Get-Content $p -ErrorAction SilentlyContinue).Count-1)}}catch{};return 0}
Beat 'stage1 launch parallel discovery'
$jobs=@()
$jobs += Start-Job -Name parcel_master_search -ScriptBlock { param($Roots,$Estate)
  $out=Join-Path $Estate 'real100_parcel_master_candidates_20260524.csv'
  'path,bytes,matched_terms' | Set-Content -Encoding UTF8 $out
  foreach($r in $Roots){if(Test-Path $r){Get-ChildItem -Path $r -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Name -match 'parcel|parsel|land|geometry|group|ready|sell|sales'} | Select-Object -First 200 | ForEach-Object { ('"'+$_.FullName+'",'+$_.Length+',"name_match"') | Add-Content -Encoding UTF8 $out }}}
} -ArgumentList $Roots,$Estate
$jobs += Start-Job -Name verified_agent_search -ScriptBlock { param($Roots,$Estate)
  $out=Join-Path $Estate 'real100_verified_agent_source_candidates_20260524.csv'
  'path,bytes,matched_terms' | Set-Content -Encoding UTF8 $out
  foreach($r in $Roots){if(Test-Path $r){Get-ChildItem -Path $r -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Name -match 'estate|agent|contact|branch|company|source|evidence'} | Select-Object -First 300 | ForEach-Object { ('"'+$_.FullName+'",'+$_.Length+',"name_match"') | Add-Content -Encoding UTF8 $out }}}
} -ArgumentList $Roots,$Estate
$jobs += Start-Job -Name candidate_quality -ScriptBlock { param($Estate)
  $cand=Join-Path $Estate 'estate_agent_candidates_from_local_artifacts_003.csv'
  $out=Join-Path $Estate 'real100_candidate_quality_20260524.json'
  $rows=0; $bytes=0; $exists=Test-Path $cand
  if($exists){$rows=[Math]::Max(0,(Get-Content $cand -ErrorAction SilentlyContinue).Count-1); $bytes=(Get-Item $cand).Length}
  @{candidate_file=$cand;exists=$exists;rows=$rows;bytes=$bytes;is_verified_directory=$false;reason='candidate artifact is not enough for production import without row-level source_url/evidence verification'} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $out
} -ArgumentList $Estate
$jobs += Start-Job -Name contract_check -ScriptBlock { param($Estate)
  $out=Join-Path $Estate 'real100_contract_check_20260524.json'
  $files=@('estate004_coverage_mapping_contract_parallel100.md','estate005_trust_truth_scoring_contract_parallel100.md','estate006_verified_export_template_parallel100.csv','estate007_parcel_join_contract_parallel100.md','estate_app_lookup_contract_parallel100.md','estate_db_dry_run_contract_parallel100.sql','estate_codex_manifest_parallel100.json')
  $items=@(); foreach($f in $files){$p=Join-Path $Estate $f; $items+=@{file=$f;exists=(Test-Path $p);bytes=$(try{if(Test-Path $p){(Get-Item $p).Length}else{0}}catch{0})}}
  $items | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $out
} -ArgumentList $Estate
Beat 'stage1 wait jobs'
Wait-Job -Job $jobs -Timeout 900 | Out-Null
$jobs | Receive-Job -ErrorAction SilentlyContinue | Out-Null
$jobs | Remove-Job -Force -ErrorAction SilentlyContinue
Beat 'stage2 dependency gate'
$parcelCand=Join-Path $Estate 'real100_parcel_master_candidates_20260524.csv'
$agentCand=Join-Path $Estate 'real100_verified_agent_source_candidates_20260524.csv'
$candidateQuality=Join-Path $Estate 'real100_candidate_quality_20260524.json'
$contractCheck=Join-Path $Estate 'real100_contract_check_20260524.json'
$parcelRows=SafeCountRows $parcelCand
$agentRows=SafeCountRows $agentCand
$verifiedRowsFile=Join-Path $Estate 'estate_agent_verified_export_dryrun_006.csv'
$verifiedRows=SafeCountRows $verifiedRowsFile
$contractsOk=$false
try{$cc=Get-Content $contractCheck -Raw | ConvertFrom-Json; $contractsOk=(@($cc)|Where-Object{-not $_.exists}).Count -eq 0}catch{}
$realParcelMasterReady=$parcelRows -gt 0
$verifiedAgentRowsReady=$verifiedRows -gt 0
$canReal100=($realParcelMasterReady -and $verifiedAgentRowsReady -and $contractsOk)
$status=if($canReal100){'real_100_ready_for_user_db_approval'}else{'blocked_external_data_required'}
$progress=if($canReal100){100}else{92}
$blockers=@()
if(-not $realParcelMasterReady){$blockers+='real TerraYield parcel master/export with parcel_id and parcel_group_id not proven'}
if(-not $verifiedAgentRowsReady){$blockers+='verified estate-agent rows with source evidence not present; candidate rows are not enough'}
if(-not $contractsOk){$blockers+='one or more technical contract artifacts missing'}
$summary=[ordered]@{task_id=$TaskId;status=$status;overall_progress=$progress;db_write=$false;production_deploy=$false;fake_data=$false;parcel_candidate_rows=$parcelRows;agent_candidate_files=$agentRows;verified_agent_rows=$verifiedRows;contracts_ok=$contractsOk;blockers=$blockers;outputs=@($parcelCand,$agentCand,$candidateQuality,$contractCheck)}
$summary | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $Result '5_1_real_100_parallel_discovery_result.json')
@('# 5.1 Real 100 Parallel Discovery Report','',('Generated: '+(Get-Date -Format s)),('Status: '+$status),('Progress: '+$progress),'','## Blockers') + ($blockers | ForEach-Object {'- '+$_}) + @('','DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false','No fake 100 accepted.') | Set-Content -Encoding UTF8 (Join-Path $Result '5_1_real_100_parallel_discovery_report.md')
@('# 5.1 Real 100 Parallel Discovery','status='+$status,'overall_progress='+$progress,'message=finished','db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb
exit 0
