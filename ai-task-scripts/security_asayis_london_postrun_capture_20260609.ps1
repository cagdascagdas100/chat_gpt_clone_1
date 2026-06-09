$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

$StartedAt = (Get-Date).ToString('o')
$RepoRoot = (Get-Location).Path
$TaskId = 'security-asayis-london-postrun-capture-20260609'
$PilotScript = Join-Path $RepoRoot 'ai-task-scripts\security_asayis_london_pilot_001_20260609.ps1'
$RepoOutDir = Join-Path $RepoRoot 'ai-results'
$RepoStatusDir = Join-Path $RepoRoot 'docs\chatgpt_status'
$FWorkRoot = 'F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609'

New-Item -ItemType Directory -Force -Path $RepoOutDir, $RepoStatusDir, $FWorkRoot | Out-Null

$Capture = Join-Path $RepoOutDir 'security_london_postrun_capture_latest.txt'
$CaptureJson = Join-Path $RepoOutDir 'security_london_postrun_capture_latest.json'
$StatusMd = Join-Path $RepoStatusDir 'security_london_postrun_capture_status_20260609.md'

$Expected = @(
  (Join-Path $RepoOutDir 'security_london_pilot_latest_status.md'),
  (Join-Path $RepoOutDir 'security_london_pilot_latest_status.json'),
  (Join-Path $RepoStatusDir 'security_london_pilot_status_20260609.md')
)
$FExpected = @(
  'F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_scores_london_pilot_points.geojson',
  'F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_scores_london_pilot_polygons.geojson',
  'F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_london_pilot_summary.json',
  'F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\security_london_pilot_method_manifest.json',
  'F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\qa\london_security_color_level_matrix.csv',
  'F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\qa\london_security_acceptance.md'
)

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# Security London Postrun Capture')
$lines.Add("Task: $TaskId")
$lines.Add("Started: $StartedAt")
$lines.Add("RepoRoot: $RepoRoot")
$lines.Add("FWorkRoot: $FWorkRoot")
$lines.Add('')
$lines.Add('## Pilot Script')
$lines.Add("Path: $PilotScript")
$lines.Add("Exists: $(Test-Path $PilotScript)")

$exitCode = $null
if (Test-Path $PilotScript) {
  $lines.Add('')
  $lines.Add('## Pilot Script Output')
  try {
    $scriptOutput = powershell -ExecutionPolicy Bypass -File $PilotScript 2>&1
    foreach ($line in $scriptOutput) { $lines.Add([string]$line) }
    $exitCode = $LASTEXITCODE
  } catch {
    $lines.Add('SCRIPT_EXCEPTION=' + $_.Exception.Message)
    $exitCode = -999
  }
} else {
  $exitCode = -404
}

$repoOutputs = @()
foreach ($p in $Expected) {
  $repoOutputs += [ordered]@{ path=$p; exists=(Test-Path $p); size_bytes=($(if (Test-Path $p) { (Get-Item $p).Length } else { 0 })) }
}
$fOutputs = @()
foreach ($p in $FExpected) {
  $fOutputs += [ordered]@{ path=$p; exists=(Test-Path $p); size_bytes=($(if (Test-Path $p) { (Get-Item $p).Length } else { 0 })) }
}

$repoReady = (($repoOutputs | Where-Object { -not $_.exists }).Count -eq 0)
$fAny = (($fOutputs | Where-Object { $_.exists }).Count -gt 0)

$summary = [ordered]@{
  task_id = $TaskId
  started_at = $StartedAt
  completed_at = (Get-Date).ToString('o')
  repo_root = $RepoRoot
  f_work_root = $FWorkRoot
  pilot_script = $PilotScript
  pilot_script_exists = (Test-Path $PilotScript)
  pilot_exit_code = $exitCode
  repo_outputs = $repoOutputs
  f_outputs = $fOutputs
  repo_ready = [bool]$repoReady
  f_any_output = [bool]$fAny
  final_ready_candidate = [bool]($repoReady -and $fAny)
  guardrails = [ordered]@{ db_write=$false; ddl=$false; migration=$false; production_deploy=$false; fake_data=$false }
}

$lines.Add('')
$lines.Add('## Exit')
$lines.Add("Pilot exit code: $exitCode")
$lines.Add('')
$lines.Add('## Repo Outputs')
foreach ($o in $repoOutputs) { $lines.Add("- $($o.path): exists=$($o.exists) size=$($o.size_bytes)") }
$lines.Add('')
$lines.Add('## F Outputs')
foreach ($o in $fOutputs) { $lines.Add("- $($o.path): exists=$($o.exists) size=$($o.size_bytes)") }
$lines.Add('')
$lines.Add('## Decision')
if ($summary.final_ready_candidate) {
  $lines.Add('FINAL_READY_CANDIDATE: true')
  $lines.Add('Next: create London-only frontend overlay/popup/legend validation task.')
} else {
  $lines.Add('FINAL_READY_CANDIDATE: false')
  $lines.Add('Next: inspect missing repo/F outputs and pilot script output above.')
}

$text = $lines -join [Environment]::NewLine
Set-Content -Path $Capture -Value $text -Encoding UTF8
Set-Content -Path $StatusMd -Value $text -Encoding UTF8
Set-Content -Path $CaptureJson -Value ($summary | ConvertTo-Json -Depth 100) -Encoding UTF8
Write-Host $text
exit 0
