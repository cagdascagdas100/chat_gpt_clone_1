$ErrorActionPreference='Continue'
$Repo=$env:AAYS_REPO_ROOT
if(-not $Repo){$Repo='F:\chatgpt\chat_gpt_clone_1_main'}
$Page='security_public_safety'
$Base=Join-Path $Repo "docs\chatgpt_status\$Page"
$Out=Join-Path $Base 'runner_outputs'
$Reports=Join-Path $Base 'reports'
$Status=Join-Path $Base 'status'
$Latest=Join-Path $Repo 'outputs\england_program_parcel_matrix_20260629\security_public_safety_updates\latest_changes.json'
New-Item -ItemType Directory -Force -Path $Out,$Reports,$Status,(Split-Path $Latest -Parent)|Out-Null
function W($name,$obj){$obj|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $Out $name) -Encoding UTF8}
$now=(Get-Date).ToString('o')
$head='unknown'; try{Push-Location $Repo; $head=(git rev-parse HEAD).Trim(); Pop-Location}catch{}
$queue=Test-Path (Join-Path $Base 'queue\terrayield-046-continuation-bundle-20260703-1438.task.json')
$files=@('england_map_web\data\security_public_safety\parcel_security_scores_verified.geojson','england_map_web\data\security_public_safety\parcel_security_scores_verified.csv','england_map_web\data\security_public_safety\security_evidence_manifest.json')|ForEach-Object{@{path=$_;exists=(Test-Path (Join-Path $Repo $_))}}
$site=@(); foreach($u in @('http://127.0.0.1:8010/england_map_web/','http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=20260630-final')){try{$r=Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 8;$site+=@{url=$u;ok=$true;status=$r.StatusCode;length=$r.Content.Length}}catch{$site+=@{url=$u;ok=$false;error=$_.Exception.Message}}}
W '046A_git_sync_and_runner_state_probe.json' @{status='ok';generated_at=$now;git_head=$head;queue_exists=$queue;final_ready=$false}
W '046B_site_and_panel_probe.json' @{status='ok';generated_at=$now;site=$site;final_ready=$false}
W '046C_security_data_contract_probe.json' @{status='blocked_missing_verified_outputs';generated_at=$now;files=$files;final_ready=$false}
W '046D_official_source_discovery_probe.json' @{status='not_started_no_source_rows_created';generated_at=$now;note='No person level data and no fake rows created.';final_ready=$false}
W '046E_blocker_classifier_and_next_queue.json' @{status='blocked';generated_at=$now;blockers=@('missing verified security parcel outputs','missing browser smoke evidence');final_ready=$false}
@{page_key=$Page;task_id='terrayield-046-continuation-bundle-20260703-1438';status='probe_bundle_ran';generated_at=$now;final_ready=$false;fake_data=$false;db_write=$false}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $Status 'security_046_probe_bundle_20260703.status.json') -Encoding UTF8
"# Security 046 probe bundle result`n`nstatus=probe_bundle_ran`nfinal_ready=false`nfake_data=false`ndb_write=false`n"|Set-Content -LiteralPath (Join-Path $Reports 'security_046_probe_bundle_20260703.md') -Encoding UTF8
@{layer='Safety / Security';program_output='Security Level percent';status='PROBE_BUNDLE_RAN_BLOCKED_MISSING_VERIFIED_OUTPUTS';last_updated=$now;final_ready=$false;fake_data=$false;db_write=$false;changes=@();blockers=@('missing verified parcel CSV/GeoJSON/manifest','missing final browser smoke evidence')}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $Latest -Encoding UTF8
