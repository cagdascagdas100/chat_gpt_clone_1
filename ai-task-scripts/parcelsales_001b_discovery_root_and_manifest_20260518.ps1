$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\parcelsales_001b_discovery_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$roots = @("C:\Users\cagda\Documents\GitHub\AAYS", "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence", "C:\AAYS_GITHUB_BRIDGE_CLEAN2", "F:\AAYS_DATA", "F:\AAYS_DATA\sales_match_program")
$items = @()
foreach ($r in $roots) { $items += [pscustomobject]@{ path=$r; exists=(Test-Path -LiteralPath $r) } }
$result = [ordered]@{ task_id="parcelsales-001b-discovery-root-and-manifest-20260518"; task_namespace="PARCELSALES"; project_label="uk-historical-sales-parcel-match"; generated_at=(Get-Date).ToString("s"); mode="read_only_discovery"; bridge_root=$BridgeRoot; output_dir=$OutDir; candidate_roots=$items }
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutDir "discovery_result.json") -Encoding UTF8
$report = @("# PARCELSALES 001B Discovery Report", "", "Mode: read-only discovery", "Bridge root: $BridgeRoot", "Output dir: $OutDir", "", "## Candidate roots")
foreach ($i in $items) { $report += "- $($i.path) exists=$($i.exists)" }
$report | Set-Content -LiteralPath (Join-Path $OutDir "discovery_report.md") -Encoding UTF8
@{ proposed_next_task_id="parcelsales-002-source-inventory-and-matching-design-20260518"; proposed_script_path="parcelsales_002_source_inventory_and_matching_design_20260518.ps1" } | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $OutDir "next_task_plan.json") -Encoding UTF8
Write-Host "PARCELSALES_DISCOVERY_OUTPUT=$OutDir"
