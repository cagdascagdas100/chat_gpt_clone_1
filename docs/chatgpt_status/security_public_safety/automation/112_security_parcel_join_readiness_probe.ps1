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
$Patterns = @('*.geojson','*.json','*.csv')
$Candidates = @()
foreach($pat in $Patterns){
  Get-ChildItem -Path $Repo -Recurse -File -Filter $pat -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match 'parcel|boundary|polygon|geometry|matrix|england_map_web' } |
    Select-Object -First 80 |
    ForEach-Object { $Candidates += @{ path=$_.FullName.Replace($Repo,'').TrimStart('\'); bytes=$_.Length } }
}
$ExistingVerified = @(
  'england_map_web\data\security_public_safety\parcel_security_scores_verified.csv',
  'england_map_web\data\security_public_safety\parcel_security_scores_verified.geojson',
  'england_map_web\data\security_public_safety\security_evidence_manifest.json'
) | ForEach-Object { @{ path=$_; exists=(Test-Path (Join-Path $Repo $_)) } }
$HasCandidate = ($Candidates.Count -gt 0)
$Result = [ordered]@{
  generated_at=$Now
  status='PARCEL_JOIN_READINESS_PROBED'
  final_ready=$false
  fake_data=$false
  verified_source_rows_created=0
  candidate_file_count=$Candidates.Count
  candidate_files=$Candidates
  existing_verified_outputs=$ExistingVerified
  remaining_blockers=@('select canonical parcel geometry source','implement official source query per parcel or area','write non-empty verified joined parcel security rows')
}
$Result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $OutDir '112_security_parcel_join_readiness_probe.json') -Encoding UTF8
$Result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $DataDir 'security_parcel_join_readiness.json') -Encoding UTF8
@{ page_key=$Page; status='parcel_join_readiness_probed'; generated_at=$Now; final_ready=$false; fake_data=$false } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $StatusDir '112_security_parcel_join_readiness_probe.status.json') -Encoding UTF8
"# Security parcel join readiness probe`n`nstatus=parcel_join_readiness_probed`nfake_data=false`nfinal_ready=false`n" | Set-Content -LiteralPath (Join-Path $ReportDir '112_security_parcel_join_readiness_probe.md') -Encoding UTF8
