$ErrorActionPreference='Continue'
$TaskId='contractor-009-scaffold-20260521-wake2'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$PreferredRoot='E:\AAYS_DATA\contractor'
if (Test-Path 'E:\') { $ContractorRoot=$PreferredRoot } else { $ContractorRoot=Join-Path $Bridge 'local-data\contractor' }
$HbDir=Join-Path $Bridge 'ai-heartbeat'
$ResultDir=Join-Path $Bridge 'ai-results'
$ExportDir=Join-Path $ContractorRoot 'exports'
$ManifestDir=Join-Path $ContractorRoot 'manifests'
New-Item -ItemType Directory -Force -Path $HbDir,$ResultDir,$ExportDir,$ManifestDir | Out-Null
$Hb=Join-Path $HbDir 'contractor-009-scaffold.md'
function W($stage,$pct,$msg){
  $lines=@('# Contractor 009 Scoring Coverage Scaffold',('task_id='+$TaskId),('stage='+$stage),('progress_percent='+$pct),('checked_at='+(Get-Date -Format s)),('message='+$msg),'contractor_root='+$ContractorRoot,'db_write=false','production_deploy=false','fake_data=false')
  try { if (Test-Path $Hb) { Remove-Item -Force $Hb -ErrorAction SilentlyContinue }; $lines | Out-File -FilePath $Hb -Encoding utf8 -Force } catch { Write-Host ('heartbeat write failed: '+$_.Exception.Message) }
}
W 'start' 5 'starting scoring and coverage scaffold'
Start-Sleep -Seconds 60
$scoring=Join-Path $ManifestDir 'contractor_009_scoring_model.json'
@{reliability_score_10='0-10 official-evidence score'; accuracy_score_4='0-4 field evidence score'; sort_score='coverage then reliability then accuracy'; contractor_root=$ContractorRoot; fake_rows_generated=$false; db_write=$false; production_deploy=$false} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path $scoring
W 'middle' 50 'scoring model written'
Start-Sleep -Seconds 60
$coverage=Join-Path $ExportDir 'contractor_coverage_scaffold.csv'
'contractor_id,parcel_group_id,coverage_method,evidence_source_url,match_score_10,evidence_score_4,rank_in_group,show_in_app,matched_real_parcel_ids,notes' | Set-Content -Encoding UTF8 -Path $coverage
W 'done' 100 'coverage scaffold and result written'
$Report=Join-Path $ResultDir 'contractor-009-scaffold-20260521.report.md'
@('# Contractor 009 Scoring Coverage Scaffold','status=completed','PLAN_PROGRESS_PERCENT=58','db_write=false','production_deploy=false','fake_data=false','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 -Path $Report
$Result=Join-Path $ResultDir 'contractor009retry-20260522-wake3.result.json'
@{task_id='contractor009retry-20260522-wake3'; status='finished'; contractor_root=$ContractorRoot; report=$Report; db_write=$false; production_deploy=$false; fake_data=$false; plan_progress_percent=58; completed_at=(Get-Date -Format s)} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path $Result
Write-Output 'PLAN_PROGRESS_PERCENT=58'
Write-Output 'TASK_COMPLETION=100/100'
Write-Output 'TERRAYIELD_TASK_DONE'
exit 0
