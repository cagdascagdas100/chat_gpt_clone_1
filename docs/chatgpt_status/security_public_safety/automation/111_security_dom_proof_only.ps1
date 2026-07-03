$ErrorActionPreference = 'Stop'
$Repo = $env:AAYS_REPO_ROOT
if (-not $Repo) { $Repo = (git rev-parse --show-toplevel).Trim() }
$Page = 'security_public_safety'
$Base = Join-Path $Repo "docs\chatgpt_status\$Page"
$OutDir = Join-Path $Base 'runner_outputs'
$ReportDir = Join-Path $Base 'reports'
$StatusDir = Join-Path $Base 'status'
New-Item -ItemType Directory -Force -Path $OutDir,$ReportDir,$StatusDir | Out-Null
$Now = (Get-Date).ToString('o')
$Urls = @('http://127.0.0.1:8010/england_map_web/','http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=20260630-final')
$Proof = foreach($u in $Urls){
  try {
    $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 8
    $c = [string]$r.Content
    @{ url=$u; ok=$true; status=$r.StatusCode; length=$c.Length; has_terrayield=($c -match 'TerraYield'); has_matrix=($c -match 'Matrix'); has_security=($c -match 'Security|Safety|security'); final_ready=$false }
  } catch {
    @{ url=$u; ok=$false; error=$_.Exception.Message; final_ready=$false }
  }
}
@{ generated_at=$Now; status='DOM_PROOF_RECORDED'; final_ready=$false; fake_data=$false; dom_proof=$Proof } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutDir '111_security_dom_proof_only.json') -Encoding UTF8
@{ page_key=$Page; status='dom_proof_recorded'; generated_at=$Now; final_ready=$false; fake_data=$false } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $StatusDir '111_security_dom_proof_only.status.json') -Encoding UTF8
"# Security DOM proof only`n`nstatus=dom_proof_recorded`nfake_data=false`nfinal_ready=false`n" | Set-Content -LiteralPath (Join-Path $ReportDir '111_security_dom_proof_only.md') -Encoding UTF8
