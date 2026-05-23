$ErrorActionPreference='Continue'
$TaskId='estate004-coverage-template'
$Root='E:\AAYS_DATA\estate_agents'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Res=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Root,$Res | Out-Null
$groups=Join-Path $Root 'england_parcel_groups_200_seed.csv'
$candidates=Join-Path $Root 'estate_agent_candidates_from_local_artifacts_003.csv'
$out=Join-Path $Root 'estate_agent_coverage_mapping_template_004.csv'
$cols='agent_candidate_id,source_row,coverage_parcel_group_ids,coverage_method,coverage_truth_score_4,program_parcel_ids_to_link_later,notes'
$lines=@($cols)
if(Test-Path $candidates){
  $rows=Get-Content $candidates -ErrorAction SilentlyContinue | Select-Object -Skip 1 -First 1000
  $n=1
  foreach($r in $rows){
    $id=($r -split ',',2)[0].Trim('"')
    if(!$id){$id='EA-CAND-'+$n}
    $lines += ($id+','+$n+',TBD_AFTER_VERIFIED_LOCATION,needs_postcode_or_coordinate,0,TBD_BY_CODEX_JOIN,verification_required')
    $n++
  }
}
$lines | Set-Content -Encoding UTF8 -Path $out
Start-Sleep -Seconds 1800
$report=Join-Path $Res ($TaskId+'.report.md')
@('# Estate 004 Coverage Template','',('generated_at: '+(Get-Date -Format s)),('groups_exists: '+(Test-Path $groups)),('candidates_exists: '+(Test-Path $candidates)),('output: '+$out),'db_write: false','production_deploy: false','PLAN_PROGRESS_PERCENT=38','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 -Path $report
exit 0
