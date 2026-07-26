$ErrorActionPreference = 'Stop'
$Repo = $env:AAYS_REPO_ROOT
if (-not $Repo) { $Repo = (git rev-parse --show-toplevel).Trim() }
$Page = 'security_public_safety'
$DataDir = Join-Path $Repo 'england_map_web\data\security_public_safety'
$OutDir = Join-Path $Repo "docs\chatgpt_status\$Page\runner_outputs"
$ReportDir = Join-Path $Repo "docs\chatgpt_status\$Page\reports"
$StatusDir = Join-Path $Repo "docs\chatgpt_status\$Page\status"
$LatestDir = Join-Path $Repo 'outputs\england_program_parcel_matrix_20260629\security_public_safety_updates'
New-Item -ItemType Directory -Force -Path $DataDir,$OutDir,$ReportDir,$StatusDir,$LatestDir | Out-Null
$Now = (Get-Date).ToString('o')
$Csv = Join-Path $DataDir 'parcel_security_scores_verified.csv'
$Geo = Join-Path $DataDir 'parcel_security_scores_verified.geojson'
$Manifest = Join-Path $DataDir 'security_evidence_manifest.json'
'parcel_id,security_score,security_level,source_count,evidence_status' | Set-Content -LiteralPath $Csv -Encoding UTF8
@{ type='FeatureCollection'; name='parcel_security_scores_verified'; generated_at=$Now; final_ready=$false; fake_data=$false; verified_row_count=0; evidence_status='no_verified_security_source_rows_available'; features=@() } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Geo -Encoding UTF8
@{ layer='Safety / Security'; program_output='Security Level percent'; generated_at=$Now; final_ready=$false; fake_data=$false; person_level_data=$false; verified_row_count=0; source_count=0; status='NO_VERIFIED_SECURITY_SOURCE_ROWS_AVAILABLE'; notes=@('Files are intentionally empty except schema because no verified security source rows are available in repo context.'); required_next_evidence=@('official security source discovery','parcel join method','browser smoke screenshot or DOM proof') } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Manifest -Encoding UTF8
$Urls = @('http://127.0.0.1:8010/england_map_web/','http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=20260630-final')
$Smoke = foreach($u in $Urls){ try { $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 8; @{url=$u; ok=$true; status=$r.StatusCode; length=$r.Content.Length} } catch { @{url=$u; ok=$false; error=$_.Exception.Message} } }
@{ generated_at=$Now; status='EMPTY_VERIFIED_OUTPUTS_WRITTEN_SMOKE_PROBED'; final_ready=$false; fake_data=$false; verified_outputs_exist=$true; browser_smoke=$Smoke } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutDir '110_security_verified_empty_outputs_and_smoke.json') -Encoding UTF8
@{ page_key=$Page; status='verified_empty_outputs_written'; generated_at=$Now; final_ready=$false; fake_data=$false } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $StatusDir '110_security_verified_empty_outputs_and_smoke.status.json') -Encoding UTF8
"# Security verified empty outputs and smoke`n`nstatus=verified_empty_outputs_written`nverified_row_count=0`nfake_data=false`nfinal_ready=false`n" | Set-Content -LiteralPath (Join-Path $ReportDir '110_security_verified_empty_outputs_and_smoke.md') -Encoding UTF8
@{ layer='Safety / Security'; program_output='Security Level percent'; status='VERIFIED_EMPTY_OUTPUTS_WRITTEN_REQUIRES_REAL_SOURCE_ROWS'; last_updated=$Now; final_ready=$false; fake_data=$false; changes=@('created schema-valid empty verified CSV, GeoJSON, and manifest'); blockers=@('no verified official security source rows','missing final browser screenshot or DOM proof') } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $LatestDir 'latest_changes.json') -Encoding UTF8
