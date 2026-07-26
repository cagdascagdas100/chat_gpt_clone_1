$ErrorActionPreference = "Stop"
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { "F:\chatgpt\chat_gpt_clone_1_main" }
$inputPath = Join-Path $repoRoot "docs\chatgpt_status\distance_property_types\inputs\distance_property_types_source_candidates.csv"
$reportDir = Join-Path $repoRoot "docs\chatgpt_status\distance_property_types\reports"
$dataDir = Join-Path $repoRoot "england_map_web\data\distance_property_types"
New-Item -ItemType Directory -Force -Path $reportDir,$dataDir | Out-Null
$progressMd = Join-Path $reportDir "distance_property_types_progress_latest.md"
$manifestJson = Join-Path $dataDir "distance_property_types_evidence_manifest.json"
$rows = @()
$blockers = @()
if (Test-Path $inputPath) { $rows = @(Import-Csv $inputPath) } else { $blockers += "missing_source_candidates_csv" }
if ($rows.Count -eq 0) { $blockers += "missing_real_evidence_rows" }
$status = if ($blockers.Count -eq 0) { "input_available_for_verification" } else { "blocked_waiting_real_evidence_rows" }
$report = "# Distance Property Types runner progress`n`nstatus=$status`nfinal_ready=false`ninput_rows=$($rows.Count)`nblockers=$($blockers -join ';')`n"
[System.IO.File]::WriteAllText($progressMd, $report)
@{page_key="distance_property_types"; status=$status; final_ready=$false; input_rows=$rows.Count; blockers=$blockers} | ConvertTo-Json | Set-Content -Path $manifestJson
@{status=$status; final_ready=$false; input_rows=$rows.Count; blockers=$blockers} | ConvertTo-Json
