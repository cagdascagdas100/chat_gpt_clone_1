$ErrorActionPreference = 'Continue'

$TaskId = 'security-asayis-london-official-target-plan-20260610'
$RepoRoot = (Get-Location).Path
$WorkRoot = 'F:\chatgpt\AAYS_WORK\security_asayis_london_official_target_plan_20260610'
if (-not (Test-Path 'F:\')) { $WorkRoot = Join-Path $RepoRoot 'ai-results\security_london_official_target_plan_work_20260610' }

$ManifestIn = Join-Path $RepoRoot 'ai-results\security_london_official_source_manifest_latest.json'
$OutJson = Join-Path $RepoRoot 'ai-results\security_london_official_target_plan_latest.json'
$OutMd = Join-Path $RepoRoot 'ai-results\security_london_official_target_plan_latest.md'
$StatusMd = Join-Path $RepoRoot 'docs\chatgpt_status\security_london_official_target_plan_status_20260610.md'

New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot 'ai-results') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot 'docs\chatgpt_status') | Out-Null

$manifest = $null
if (Test-Path $ManifestIn) {
  try { $manifest = Get-Content $ManifestIn -Raw | ConvertFrom-Json } catch {}
}

$candidates = @()
if ($manifest -ne $null -and $manifest.candidates -ne $null) { $candidates = @($manifest.candidates) }

$parcelTargets = @($candidates | Where-Object { $_.candidate_kind -eq 'parcel_or_title_polygon' } | Select-Object -First 4)
$crimeTargets = @($candidates | Where-Object { $_.candidate_kind -eq 'crime_or_police' } | Select-Object -First 8)
$boundaryTargets = @($candidates | Where-Object { $_.candidate_kind -eq 'boundary_or_lsoa' } | Select-Object -First 4)

$decision = 'OFFICIAL_TARGET_PLAN_REVIEW_REQUIRED'
$nextStep = 'Create resolver for missing boundary source and controlled extraction task after parcel, boundary, and crime target URLs are all selected.'
if (($parcelTargets.Count -gt 0) -and ($crimeTargets.Count -gt 0)) {
  $decision = 'OFFICIAL_TARGET_PLAN_PARTIAL_READY'
  $nextStep = 'Create boundary resolver task, then London-only extraction task; no fake data and no DB write.'
}
if (($parcelTargets.Count -gt 0) -and ($crimeTargets.Count -gt 0) -and ($boundaryTargets.Count -gt 0)) {
  $decision = 'OFFICIAL_TARGET_PLAN_READY_FOR_EXTRACTION_TASK'
  $nextStep = 'Create London-only extraction task from selected official targets; no fake data and no DB write.'
}

$result = [ordered]@{
  task_id = $TaskId
  started_at = (Get-Date).ToString('o')
  repo_root = $RepoRoot
  work_root = $WorkRoot
  manifest_input_exists = (Test-Path $ManifestIn)
  parcel_target_count = $parcelTargets.Count
  crime_target_count = $crimeTargets.Count
  boundary_target_count = $boundaryTargets.Count
  parcel_targets = $parcelTargets
  crime_targets = $crimeTargets
  boundary_targets = $boundaryTargets
  ready_for_london_build_task = $false
  decision = $decision
  next_step = $nextStep
  safety = [ordered]@{ db_write=$false; production_deploy=$false; ddl=$false; london_only=$true; migration=$false; fake_data=$false }
}

[System.IO.File]::WriteAllText($OutJson, ($result | ConvertTo-Json -Depth 12), [System.Text.UTF8Encoding]::new($false))

$md = @()
$md += '# Security London official target plan status'
$md += ''
$md += '- task_id: ' + $TaskId
$md += '- repo_root: ' + $RepoRoot
$md += '- work_root: ' + $WorkRoot
$md += '- manifest_input_exists: ' + (Test-Path $ManifestIn)
$md += '- parcel_target_count: ' + $parcelTargets.Count
$md += '- crime_target_count: ' + $crimeTargets.Count
$md += '- boundary_target_count: ' + $boundaryTargets.Count
$md += '- decision: ' + $decision
$md += '- next_step: ' + $nextStep
$md += ''
$md += '## Safety'
$md += '- db_write: false'
$md += '- production_deploy: false'
$md += '- ddl: false'
$md += '- migration: false'
$md += '- fake_data: false'
[System.IO.File]::WriteAllText($OutMd, ($md -join [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
Copy-Item $OutMd $StatusMd -Force

Write-Output ('OFFICIAL_TARGET_PLAN_JSON=' + $OutJson)
Write-Output ('OFFICIAL_TARGET_PLAN_DECISION=' + $decision)
exit 0
