$ErrorActionPreference='Continue'
$TaskId='security-public-safety-boundary-root-resolver-20260612'
$PageKey='security_public_safety_low_credit_20260612'
$BridgeRoot='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$WorkRoot='F:\chatgpt\AAYS_WORK\security_public_safety_boundary_root_resolver_20260612'
if(-not (Test-Path 'F:\')){ $WorkRoot=Join-Path $BridgeRoot 'ai-results\security_public_safety_boundary_root_resolver_work_20260612' }

$StatusRoot=Join-Path $BridgeRoot "docs\chatgpt_status\$PageKey"
$ReportsDir=Join-Path $StatusRoot 'reports'
$StatusDir=Join-Path $StatusRoot 'status'
$HeartbeatDir=Join-Path $StatusRoot 'heartbeat'
$RunnerOutDir=Join-Path $StatusRoot 'runner_output'
$ResultsDir=Join-Path $BridgeRoot 'ai-results'
foreach($d in @($WorkRoot,$ReportsDir,$StatusDir,$HeartbeatDir,$RunnerOutDir,$ResultsDir)){ New-Item -ItemType Directory -Force -Path $d | Out-Null }

$Log=Join-Path $RunnerOutDir "$TaskId.log"
function Log($m){ ('['+(Get-Date -Format s)+'] '+$m) | Tee-Object -FilePath $Log -Append }

Log "start $TaskId"

$Candidates=@(
 'C:\Users\cagda\Documents\GitHub\AAYS',
 'C:\AAYS',
 $BridgeRoot
)

$Checks=@()
$Selected=$null
foreach($r in $Candidates){
  $o=[ordered]@{
    root=$r
    exists=(Test-Path $r)
    app_js=(Test-Path (Join-Path $r 'england_map_web\app.js'))
    security_overlay_js=(Test-Path (Join-Path $r 'england_map_web\security_overlay.js'))
    security_overlay_css=(Test-Path (Join-Path $r 'england_map_web\security_overlay.css'))
    summary_json=(Test-Path (Join-Path $r 'england_map_web\data\parcel_security_match_summary.json'))
    security_geojson=(Test-Path (Join-Path $r 'england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson'))
  }
  if(-not $Selected -and $o.app_js -and $o.security_overlay_js){ $Selected=$r }
  $Checks += [pscustomobject]$o
}

$Decision=if($Selected){'READY_FOR_SECURITY_FRONTEND_CONTRACT_PATCH'}else{'BLOCKED_APP_ROOT_NOT_FOUND'}
$Result=[ordered]@{
  task_id=$TaskId
  page_key=$PageKey
  selected_app_root=$Selected
  root_checks=$Checks
  decision=$Decision
  final_ready=$false
  production_complete=$false
  db_write=$false
  migration=$false
  production_deploy=$false
  fake_data=$false
  next_step=if($Selected){'Apply Security overlay popup/legend/data-contract patch, then run static acceptance probe.'}else{'Fix local app root mapping before patching.'}
  finished_at=(Get-Date -Format o)
}

$ResultPath=Join-Path $ResultsDir 'security_public_safety_boundary_root_resolver_latest.json'
$Result | ConvertTo-Json -Depth 10 | Set-Content $ResultPath -Encoding UTF8

$Report=Join-Path $ReportsDir "$TaskId.md"
@(
'# Security Public Safety Boundary Root Resolver',
'',
"decision: $Decision",
"selected_app_root: $Selected",
'final_ready: false',
'production_complete: false',
'db_write: false',
'migration: false',
'production_deploy: false',
'fake_data: false',
"result_json: $ResultPath"
) | Set-Content $Report -Encoding UTF8

Copy-Item $Report (Join-Path $StatusDir 'latest.md') -Force
@('# Security heartbeat','',"task_id: $TaskId","decision: $Decision","checked_at: $(Get-Date -Format s)") | Set-Content (Join-Path $HeartbeatDir 'latest.md') -Encoding UTF8

Log "done decision=$Decision selected_app_root=$Selected"

git -C $BridgeRoot add 'ai-results/security_public_safety_boundary_root_resolver_latest.json' "docs/chatgpt_status/$PageKey" 
git -C $BridgeRoot commit -m "Run security public safety boundary root resolver"
git -C $BridgeRoot push origin main
if($Selected){ exit 0 } else { exit 2 }
