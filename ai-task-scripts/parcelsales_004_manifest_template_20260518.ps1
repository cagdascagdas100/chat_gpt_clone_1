$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\parcelsales_004_manifest_template_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Manifest = [ordered]@{
  task_id = "parcelsales-004-manifest-template-20260518"
  file_name = "data_sources_manifest.json"
  required_fields = @("source_name", "source_url", "licence", "retrieved_at", "evidence_ref", "notes")
}
$Manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $OutDir "data_sources_manifest_template.json") -Encoding UTF8
$Lines = @("source_name", "source_url", "licence", "retrieved_at", "evidence_ref", "notes")
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "manifest_fields.txt") -Encoding UTF8
Write-Host "PARCELSALES_004_OUTPUT=$OutDir"
