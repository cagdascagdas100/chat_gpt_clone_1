$B='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$O=Join-Path $B 'ai-results'
$H=Join-Path $B 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $O,$H | Out-Null
$T='sh106944-status-inventory-r1'
$R=Join-Path $O ($T+'.result.json')
$Now=Get-Date -Format s
@{task_id=$T;status='finished';official_sales_rows=106944;verified_rows=0;verified_parcels=0;final_gate='BLOCKED_MISSING_OFFICIAL_BRIDGE';review_gate='NOT_READY_FOR_AUTO_ACCEPT';db_write=$false;production_deploy=$false;fake_data=$false;next_action='Need authoritative NPS Title_No UPRN polygon and address to UPRN bridge before verified publish';completed_at=$Now} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $R
@('# AAYS Portable Task Runner Fixed','','Time: '+$Now,'Status: finished','TaskId: '+$T,'Message: SH106944 inventory status recorded','DBWrite: false','ProductionDeploy: false','FakeData: false') | Set-Content -Encoding UTF8 (Join-Path $H 'portable-runner.md')
exit 0
