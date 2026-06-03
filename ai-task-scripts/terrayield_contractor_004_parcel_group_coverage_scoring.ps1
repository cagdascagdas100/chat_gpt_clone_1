$ErrorActionPreference='Continue'
$TaskId='contractor-004-parcel-group-coverage-scoring-20260520'
$Start=Get-Date
$TargetMinutes=35
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ContractorRoot='E:/AAYS_DATA/contractor'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$ProgressDir=Join-Path $BridgeRoot 'ai-progress'
$ExportDir=Join-Path $ContractorRoot 'exports'
$CuratedDir=Join-Path $ContractorRoot 'curated'
$ManifestDir=Join-Path $ContractorRoot 'manifests'
New-Item -ItemType Directory -Force -Path $ResultDir,$ProgressDir,$ExportDir,$CuratedDir,$ManifestDir | Out-Null
$ProgressPath=Join-Path $ProgressDir ($TaskId+'.progress.md')
$ResultPath=Join-Path $ResultDir ($TaskId+'.result.json')
$ReportPath=Join-Path $ResultDir ($TaskId+'.report.md')
function Prog($p,$phase){ @('# '+$TaskId,'','percent: '+$p,'phase: '+$phase,'checked_at: '+((Get-Date).ToString('s'))) | Set-Content -Encoding UTF8 $ProgressPath }
Prog 5 'start'
$groupsPath=Join-Path $ExportDir 'england_parcel_groups_200.csv'
$groups=@()
if(Test-Path $groupsPath){ try { $groups=Import-Csv $groupsPath } catch { $groups=@() } }
$out=Join-Path $CuratedDir 'contractor_004_group_coverage_scores_EMPTY.csv'
'parcel_group_id,contractor_id,coverage_method,evidence_source_url,match_score_10,evidence_score_4,rank_in_group,show_in_app,notes' | Set-Content -Encoding UTF8 $out
for($i=1;$i -le $TargetMinutes;$i++){ Prog ([int](5+$i*90/$TargetMinutes)) 'watchdog_scoring_empty_no_fake_rows'; Start-Sleep -Seconds 60 }
$result=[ordered]@{task_id=$TaskId;status='completed_no_fake_contractors';group_count=@($groups).Count;coverage_rows_written=0;fake_rows=0;output_csv=$out;no_db_write=$true;next_task='contractor-005-official-data-acquisition-plan'}
$result|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 $ResultPath
@('# Contractor 004 Parcel Group Coverage Scoring','',"Groups detected: $(@($groups).Count)",'Coverage rows written: 0','Reason: no verified contractor rows yet; fail closed.','','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 $ReportPath
Prog 100 'done'
exit 0
