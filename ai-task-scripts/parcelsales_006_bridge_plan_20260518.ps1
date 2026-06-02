$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\parcelsales_006_bridge_plan_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Lines = @()
$Lines += "# PARCELSALES 006 Bridge Plan"
$Lines += ""
$Lines += "Goal: plan safe bridge from official sales records to parcel or title polygon records."
$Lines += ""
$Lines += "Required bridge options:"
$Lines += "- transaction id to deterministic parcel or title reference"
$Lines += "- address plus postcode to unique property reference"
$Lines += "- property reference to parcel or title polygon"
$Lines += "- geocoded point to polygon only when unique and documented"
$Lines += ""
$Lines += "Guardrails:"
$Lines += "- uncertain rows stay unmatched"
$Lines += "- candidate rows are not verified rows"
$Lines += "- each exported row needs source and evidence fields"
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "bridge_plan.md") -Encoding UTF8
Write-Host "PARCELSALES_006_OUTPUT=$OutDir"
