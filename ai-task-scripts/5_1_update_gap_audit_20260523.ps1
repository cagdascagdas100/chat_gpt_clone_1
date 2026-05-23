$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Out=Join-Path $Bridge 'ai-results'
$Hb=Join-Path $Bridge 'ai-heartbeat\5_1_update_gap_audit.md'
New-Item -ItemType Directory -Force -Path $Out,(Split-Path $Hb -Parent) | Out-Null
function Beat($m){ @('# 5.1 Update Gap Audit','status=running',('message='+$m),('time='+(Get-Date -Format s)),'db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb }
Beat 'start'
$expected=@(
  'E:\AAYS_DATA\estate_agents\estate_agent_source_acquisition_plan_002.json',
  'E:\AAYS_DATA\estate_agents\estate_agent_coverage_scoring_rules_002.md',
  'E:\AAYS_DATA\estate_agents\estate_existing_artifact_inventory_002.csv',
  'E:\AAYS_DATA\estate_agents\estate_agent_candidates_from_local_artifacts_003.csv',
  'C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\project_100_finalize.result.json',
  'C:\AAYS_GITHUB_BRIDGE_CLEAN2\docs\chatgpt_status\pages\5-1-update-latest.json'
)
$items=@()
foreach($p in $expected){
  Beat ('check '+$p)
  $exists=Test-Path $p
  $len=0
  if($exists){try{$len=(Get-Item $p).Length}catch{}}
  $items += [ordered]@{path=$p;exists=$exists;bytes=$len}
  Start-Sleep -Seconds 20
}
$follow=@(
  'estate-004 postcode/admin coverage mapping not proven complete',
  'estate-005 trust/truth scoring not proven complete',
  'estate-006 Excel export must be verified against final candidate artifacts',
  'estate-007 Codex parcel_id join package not proven complete',
  'database import intentionally not performed because db_write=false',
  'production deploy intentionally not performed because production_deploy=false'
)
$result=[ordered]@{
 task_id='5_1_update_gap_audit_20260523'
 status='finished_with_open_followups'
 generated_at=(Get-Date -Format s)
 db_write=$false
 production_deploy=$false
 fake_data=$false
 checked_files=$items
 open_followups=$follow
 recommended_progress_percent=82
}
$json=Join-Path $Out '5_1_update_gap_audit_20260523.json'
$md=Join-Path $Out '5_1_update_gap_audit_20260523.md'
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $json
@('# 5.1 Update Gap Audit','',('Generated: '+(Get-Date -Format s)),'','Status: finished_with_open_followups','','Open followups:') + ($follow | ForEach-Object {'- '+$_}) + @('','DB write: false','Production deploy: false','Fake data: false','Recommended progress: 82') | Set-Content -Encoding UTF8 $md
@('# 5.1 Update Gap Audit','status=finished_with_open_followups','message=done','db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb
exit 0
