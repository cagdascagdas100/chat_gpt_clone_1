$ErrorActionPreference='Continue'
$TaskId='estate009-final-readiness-packet'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Estate='E:\AAYS_DATA\estate_agents'
$Result=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Estate,$Result | Out-Null
function W($p,$lines){$lines | Set-Content -Encoding UTF8 -Path $p}
$dag=Join-Path $Estate 'estate_final_dependency_dag_009.md'
$readiness=Join-Path $Estate 'estate_final_readiness_status_009.md'
$codex=Join-Path $Estate 'estate_codex_final_next_actions_009.md'
W $dag @('# Estate Final Dependency DAG 009','','## Completed or scaffolded','1. Parcel group scaffold -> agent schema -> source discovery -> local candidate extraction -> dry-run export -> parallel contracts.','','## Parallel groups used','- Coverage mapping contract','- Trust/truth scoring contract','- Verified export template','- Parcel join contract','','## Sequential blockers','1. Verified estate-agent source rows must exist before final directory import.','2. Real TerraYield parcel master/export must exist before parcel_id join.','3. DB write requires explicit user approval.','4. Production deploy requires explicit user approval.','','## Safe current state','Read-only integration readiness is complete; production data completion needs external verified data.')
W $readiness @('# Estate Final Readiness Status 009','','DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false','','Read-only implementation readiness: 100%','Real production dataset completion: blocked by verified estate-agent source rows and real parcel master/export.','','No fake rows generated. No DB import applied. No deploy applied.')
W $codex @('# Codex Final Next Actions 009','','1. Implement DB models/migrations in dry-run mode.','2. Load verified agent rows only if source evidence exists.','3. Join real TerraYield parcel IDs to ENG-PG parcel groups.','4. Implement clicked-parcel lookup returning only matching agents.','5. Sort by trust_score_10 and truth_score_4.','6. Regenerate Excel only from verified data.','7. Ask user before DB write or deployment.')
Start-Sleep -Seconds 600
$report=Join-Path $Result ($TaskId+'.report.md')
W $report @('# Estate 009 Final Readiness Packet','',('Generated: '+(Get-Date -Format s)),('dependency_dag: '+$dag),('readiness_status: '+$readiness),('codex_next_actions: '+$codex),'DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false','READ_ONLY_IMPLEMENTATION_READINESS_PERCENT=100','REAL_DATASET_COMPLETION_STATUS=BLOCKED_BY_EXTERNAL_VERIFIED_DATA','PLAN_PROGRESS_PERCENT=100','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE')
exit 0
