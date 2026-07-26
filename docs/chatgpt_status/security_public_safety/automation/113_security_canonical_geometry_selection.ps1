$ErrorActionPreference = 'Stop'
$Repo = $env:AAYS_REPO_ROOT
if (-not $Repo) { $Repo = (git rev-parse --show-toplevel).Trim() }
$Page = 'security_public_safety'
$Base = Join-Path $Repo "docs\chatgpt_status\$Page"
$OutDir = Join-Path $Base 'runner_outputs'
$ReportDir = Join-Path $Base 'reports'
$StatusDir = Join-Path $Base 'status'
$DataDir = Join-Path $Repo 'england_map_web\data\security_public_safety'
New-Item -ItemType Directory -Force -Path $OutDir,$ReportDir,$StatusDir,$DataDir | Out-Null
$Now = (Get-Date).ToString('o')
$Candidates = @(
  'docs\chatgpt_status\aays1\geometry_review_3of4\all_1264_real_geometry_3of4.geojson',
  'england_map_web\data\geometry_review_3of4\visible_225_real_geometry_3of4.geojson',
  'docs\chatgpt_status\aays1\geometry_review_3of4\visible_225_real_geometry_3of4.geojson'
)
$Checks = foreach($rel in $Candidates){
  $p = Join-Path $Repo $rel
  if(Test-Path $p){ @{ path=$rel; exists=$true; bytes=(Get-Item $p).Length } } else { @{ path=$rel; exists=$false; bytes=0 } }
}
$Selected = ($Checks | Where-Object { $_.exists -and $_.path -match 'all_1264' } | Select-Object -First 1)
if(-not $Selected){ $Selected = ($Checks | Where-Object { $_.exists } | Select-Object -First 1) }
$Result = [ordered]@{
  generated_at=$Now
  status=$(if($Selected){'CANONICAL_GEOMETRY_SELECTED'}else{'NO_CANONICAL_GEOMETRY_FOUND'})
  final_ready=$false
  fake_data=$false
  selected_geometry=$(if($Selected){$Selected.path}else{$null})
  selected_geometry_bytes=$(if($Selected){$Selected.bytes}else{0})
  candidates=$Checks
  verified_source_rows_created=0
  next_step='implement official security source query and parcel join using selected geometry'
}
$Result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutDir '113_security_canonical_geometry_selection.json') -Encoding UTF8
$Result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $DataDir 'security_canonical_geometry_selection.json') -Encoding UTF8
@{ page_key=$Page; status=$Result.status; generated_at=$Now; final_ready=$false; fake_data=$false } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $StatusDir '113_security_canonical_geometry_selection.status.json') -Encoding UTF8
"# Security canonical geometry selection`n`nstatus=$($Result.status)`nselected_geometry=$($Result.selected_geometry)`nfake_data=false`nfinal_ready=false`n" | Set-Content -LiteralPath (Join-Path $ReportDir '113_security_canonical_geometry_selection.md') -Encoding UTF8
